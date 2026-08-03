from __future__ import annotations

import json
import math
import os
from typing import Any, Literal, TypedDict

from pydantic import BaseModel

import httpx
from dotenv import load_dotenv
from IPython.display import Image, Markdown, display
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langchain.agents import create_agent
import gradio as gr

load_dotenv(override=True)

def make_llm():
    openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    print(f"OPENAI_API_KEY loaded in make_llm: {'*****' if openai_api_key else 'None'}")
    return ChatOpenAI(
        model_name="gpt-3.5-turbo",  # or another supported OpenRouter model
        temperature=0,
        openai_api_key=openai_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

class LocationParseError(BaseModel):
    ok: Literal[False] = False
    reason: str
    latitude: float | None = None
    longitude: float | None = None


class LocationParseSuccess(BaseModel):
    ok: Literal[True] = True
    latitude: float
    longitude: float


def _finalize_coordinates(latitude: float, longitude: float) -> LocationParseSuccess | LocationParseError:
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return LocationParseError(reason="non_finite", latitude=latitude, longitude=longitude)
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return LocationParseError(reason="out_of_range", latitude=latitude, longitude=longitude)
    return LocationParseSuccess(latitude=latitude, longitude=longitude)


@tool
def submit_user_coordinates(latitude: float, longitude: float) -> str:
    """Call after you (the agent) extracted WGS84 numbers from the user's message. Validates ranges and returns JSON: ok, latitude, longitude (or ok:false with reason). The app uses ok:true for OpenStreetMap (Overpass) search."""
    return _finalize_coordinates(latitude, longitude).model_dump_json(exclude_none=True)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "PR/1.0"

#find the distance between two points on the earth using the haversine formula
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# --- OSM Overpass API utility ---
def overpass_amenity(latitude: float, longitude: float, radius_m: int, amenity: str):
    """Query Overpass API for amenities near a point."""
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="{amenity}"](around:{radius_m},{latitude},{longitude});
      way["amenity"="{amenity}"](around:{radius_m},{latitude},{longitude});
      relation["amenity"="{amenity}"](around:{radius_m},{latitude},{longitude});
    );
    out center;
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = httpx.post(OVERPASS_URL, data=query, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for el in data.get("elements", []):
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            name = el.get("tags", {}).get("name", "(no name)")
            results.append({"name": name, "lat": lat, "lon": lon})
        return results
    except Exception as e:
        return []

@tool
def parking_specialist_search_near_user(latitude: float, longitude: float, radius_m: int = 2500) -> str:
    """Parking specialist: list OSM parkings near the user, nearest first."""
    rows = overpass_amenity(latitude, longitude, radius_m, "parking")
    return json.dumps({"parkings": rows, "count": len(rows)})


@tool
def restaurant_specialist_search_near_point(latitude: float, longitude: float, radius_m: int = 800) -> str:
    """Restaurant specialist: list OSM restaurants near a point."""
    rows = overpass_amenity(latitude, longitude, radius_m, "restaurant")
    return json.dumps({"restaurants": rows, "count": len(rows)})


llm = make_llm()

REPLY_SYSTEM = """You are the **Reply agent** — you talk with the user until you have valid coordinates, then the app sends those coordinates to the parking/restaurant search (OpenStreetMap via Overpass).

- On the very first message, greet the user and offer help finding parking near a restaurant.
- If the user says 'yes' or agrees, immediately ask for a Google Maps link or coordinates. Do NOT repeat the greeting.
- If they ask what you can do, explain and ask if they want that search.
- When they want search, ask for a **Google Maps** link (look for `@lat,lng` or `?q=lat,lng`) or **two decimal numbers** (latitude, longitude in WGS84).
- When their message clearly contains numeric coordinates, **you** read them from the text (order: latitude then longitude for a plain pair; in many map URLs the first number after `@` is latitude). Call **submit_user_coordinates** once with those two floats.
- Never call the tool with guessed coordinates from a city or place name alone — only when numbers appear in the message.
- If the tool returns **ok:false** (e.g. out_of_range), explain and ask for a corrected location.
- If **ok:true**, confirm briefly — the **application** will run the OSM search and append results below your reply.
- Keep replies short unless they ask for detail."""

PARKING_SPECIALIST_PROMPT = """You are the parking specialist. When given latitude and longitude, call "
"parking_specialist_search_near_user once with those numbers. Do not invent coordinates."""

RESTAURANT_SPECIALIST_PROMPT = """You collaborate with the parking specialist. You receive JSON with a list `parkings` sorted by distance from the user. "
"For EACH parking in order, call restaurant_specialist_search_near_point with that parking's lat and lng "
"until a call returns count > 0, or you have tried all parkings. Report which parking index worked."""

reply_agent = create_agent(
    llm,
    [submit_user_coordinates],
    system_prompt=REPLY_SYSTEM,
)

parking_agent = create_agent(
    llm,
    [parking_specialist_search_near_user],
    system_prompt=PARKING_SPECIALIST_PROMPT,
)

restaurant_agent = create_agent(
    llm,
    [restaurant_specialist_search_near_point],
    system_prompt=RESTAURANT_SPECIALIST_PROMPT,
)

def last_tool_content(messages: list, tool_name: str) -> str | None:
    for m in reversed(messages):
        if isinstance(m, ToolMessage) and m.name == tool_name:
            return str(m.content)
    return None


def extract_submitted_coordinates(messages: list) -> dict[str, Any] | None:
    raw = last_tool_content(messages, "submit_user_coordinates")
    if raw is None:
        return None
    return json.loads(raw)


def extract_parking_json(messages: list) -> str | None:
    return last_tool_content(messages, "parking_specialist_search_near_user")


def last_assistant_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage) and (m.content or '').strip():
            return str(m.content)
    return ""

class SearchState(TypedDict, total=False):
    latitude: float
    longitude: float
    parking_json: str | None
    restaurant_messages: list | None
    final_markdown: str


def node_parking(state: SearchState) -> SearchState:
    lat, lng = state["latitude"], state["longitude"]
    text = (
        f"Find parking options near user latitude {lat} and longitude {lng}. "
        "Call parking_specialist_search_near_user once."
    )
    out = parking_agent.invoke({"messages": [HumanMessage(text)]})
    msgs = out.get('messages', [])
    pj = extract_parking_json(msgs) or "{}"
    return {"parking_json": pj}


def node_restaurant(state: SearchState) -> SearchState:
    lat, lng = state["latitude"], state["longitude"]
    parking_json = state.get("parking_json") or "{}"
    text = (
        f"User is at latitude {lat}, longitude {lng}.\n\n"
        f"Parking specialist JSON:\n{parking_json}\n\n"
        "Try each parking in order: call restaurant_specialist_search_near_point for each parking's lat/lng "
        "until restaurants appear, or all parkings are exhausted."
    )

    out = restaurant_agent.invoke(
        {"messages": [HumanMessage(text)]},
        config={"recursion_limit": 20},
    )
    return {"restaurant_messages": out.get("messages", [])}


def node_summarize(state: SearchState) -> SearchState:
    summary_llm = make_llm()
    rest_msgs = state.get('restaurant_messages') or []
    rest_tail = ''
    for m in rest_msgs[-8:]:
        if isinstance(m, (AIMessage, ToolMessage)):
            rest_tail += type(m).__name__ + ": " + str(getattr(m, "content", "")) + "\n"
    sys = SystemMessage(
        content=(
            "You write concise Markdown for the user. Include: coordinates, "
            "parking summary from JSON, what the restaurant specialist tried, and the best restaurant found "
            "(if any). Mention that data comes from OpenStreetMap and may be incomplete."
        )
    )
    hum = HumanMessage(
        content=(
            f"User at lat={state['latitude']}, lng={state['longitude']}\n\n"
            f"Parking JSON:\n{state.get('parking_json')}\n\n"
            f"Restaurant agent trace (last messages):\n{rest_tail}"
        )
    )
    out = summary_llm.invoke([sys, hum])
    return {"final_markdown": out.content}


def build_search_graph() -> StateGraph:
    g = StateGraph(SearchState)
    g.add_node("parking", node_parking)
    g.add_node("restaurant", node_restaurant)
    g.add_node("summarize", node_summarize)
    g.add_edge(START, "parking")
    g.add_edge("parking", "restaurant")
    g.add_edge("restaurant", "summarize")
    g.add_edge("summarize", END)
    return g.compile()


search_graph = build_search_graph()

try:
    display(Image(search_graph.get_graph().draw_mermaid_png()))
except Exception as e:
    print("Diagram skipped:", e)

def messages_from_chat(history: list) -> list:
    msgs = []
    for pair in history or []:
        if isinstance(pair, dict):
            # Ignore dicts, only process list/tuple
            continue
        if not pair or len(pair) < 2:
            continue
        u, a = pair[0], pair[1]
        if u is not None and str(u).strip():
            msgs.append(HumanMessage(str(u)))
        if a is not None and str(a).strip():
            msgs.append(AIMessage(content=str(a)))
    return msgs


def chat_with_agents(message: str, history: list):
    message = (message or '').strip()
    if not message:
        yield history
        return

    hist = list(history or [])

    def to_gradio_dicts(pairs):
        out = []
        for pair in pairs:
            # Accept both list/tuple and dict
            if isinstance(pair, dict):
                # Already in Gradio format
                if "role" in pair and "content" in pair:
                    out.append(pair)
                continue
            if not pair or len(pair) < 2:
                continue
            user, assistant = pair[0], pair[1]
            if user is not None and str(user).strip():
                out.append({"role": "user", "content": str(user)})
            if assistant is not None and str(assistant).strip():
                out.append({"role": "assistant", "content": str(assistant)})
        return out

    # Add the new user message as a pair with a placeholder
    typing_hist = hist + [[message, '*typing…*']]
    yield to_gradio_dicts(typing_hist)

    # Only keep the last 8 exchanges to avoid context overflow
    trimmed_hist = hist[-8:] if len(hist) > 8 else hist
    prior = messages_from_chat(trimmed_hist)
    prior.append(HumanMessage(message))

    out = reply_agent.invoke({"messages": prior})
    rmsgs = out.get('messages', [])
    reply_text = last_assistant_text(rmsgs)
    if not reply_text:
        reply_text = "I could not produce a reply."

    parsed = extract_submitted_coordinates(rmsgs)
    if not parsed or not parsed.get('ok'):
        yield to_gradio_dicts(hist + [[message, reply_text]])
        return

    lat, lng = float(parsed['latitude']), float(parsed['longitude'])
    last_s: dict | None = None
    try:
        for state in search_graph.stream(
            {"latitude": lat, "longitude": lng},
            stream_mode="values",
        ):
            last_s = state
    except Exception as e:
        yield to_gradio_dicts(hist + [[message, reply_text + f"\n\n**Search error:** `{e}`"]])
        return

    search_md = (last_s or {}).get("final_markdown") or "*No search output.*"
    final = reply_text + "\n\n" + search_md
    yield to_gradio_dicts(hist + [[message, final]])


with gr.Blocks(title="Find parking near a restaurant") as demo:
    gr.Markdown(
    "Find parking near a restaurant"
    )
    chat = gr.Chatbot(label="Conversation", height=420)
    msg = gr.Textbox(
        placeholder="Type a message…",
        label="Message",
        lines=2,
    )
    send = gr.Button("Send", variant="primary")
    _inputs = [msg, chat]
    _outputs = [chat]
    send.click(chat_with_agents, _inputs, _outputs, show_progress="full").then(
        lambda: "", outputs=msg
    )
    msg.submit(chat_with_agents, _inputs, _outputs, show_progress="full").then(
        lambda: "", outputs=msg
    )

demo.launch(share=False, inline=True, debug=True)


# === TEMP: Print Mermaid for PR ===
if __name__ == "__main__":
    print("```mermaid")
    print(search_graph.get_graph().draw_mermaid())
    print("```")

# Or, if you want to use Colab's secrets manager:
# from google.colab import userdata
# os.environ["OPENROUTER_API_KEY"] = userdata.get('OPENROUTER_API_KEY')


