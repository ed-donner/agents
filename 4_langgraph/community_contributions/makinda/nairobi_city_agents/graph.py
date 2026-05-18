"""
LangGraph multi-agent workflow for Nairobi using course patterns (StateGraph, conditional edges, MemorySaver) and OpenAI.

Flow:
  local events (SQLite) → dummy-data LLM if empty → optional Serper enrichment →
  OpenWeatherMap (current + short forecast) → outfit/activities advisor →
  Chroma RAG venues → analysis LLM.

LangSmith: set LANGCHAIN_API_KEY (and optionally LANGCHAIN_PROJECT) to trace runs in
https://smith.langchain.com — enabled in config.configure_langsmith() on import.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from config import CITY, LLM_MODEL, configure_langsmith

configure_langsmith()
from dummy_events import run_dummy_data_agent
from local_db import fetch_events_text
from rag_venues import retrieve_venues_context
from serper_search import search_nairobi_events
from state import NairobiCityState
from weather_api import fetch_nairobi_forecast_digest, fetch_nairobi_weather


def node_local_events(state: NairobiCityState) -> dict:
    """Read SQLite; if empty, run the dummy-data agent to synthesize seed events."""
    city = state.get("city") or CITY
    text = fetch_events_text(city)
    if "No upcoming events found" in text:
        try:
            inserted = run_dummy_data_agent()
            text = fetch_events_text(city)
            text = f"(Seeded {inserted} synthetic local events via LLM.)\n\n{text}"
        except Exception as exc:
            text = f"{text}\nDummy data agent failed: {exc}"
    return {"city": city, "events_local": text}


def route_after_local(
    state: NairobiCityState,
) -> Literal["online_search", "merge_local"]:
    """Hit online search when the local DB still has no rows."""
    el = state.get("events_local") or ""
    if "No upcoming events found" in el:
        return "online_search"
    return "merge_local"


def node_online_search(state: NairobiCityState) -> dict:
    extra = (state.get("user_question") or "")[:200]
    online = search_nairobi_events(extra)
    combined = (state.get("events_local") or "") + "\n\n--- Web supplement (Serper) ---\n\n" + online
    return {"events_online": online, "events_combined": combined}


def node_merge_local(state: NairobiCityState) -> dict:
    return {"events_combined": state.get("events_local", "")}


def node_weather(_state: NairobiCityState) -> dict:
    current = fetch_nairobi_weather()
    forecast = fetch_nairobi_forecast_digest()
    parts = [current]
    if forecast.strip():
        parts.append(forecast)
    return {"weather_info": "\n\n".join(parts)}


def node_outfit_advisor(state: NairobiCityState) -> dict:
    """Weather-conditioned outfit and activity suggestions."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.35)
    system = SystemMessage(
        content=(
            "You advise visitors and residents in Nairobi, Kenya. "
            "Using the CURRENT CONDITIONS and SHORT-RANGE FORECAST below (temperature, "
            "humidity, wind, rain probability, expected rain), produce:\n\n"
            "## What to wear\n"
            "- Bullet points: layers, fabrics, footwear, rain gear (umbrella vs jacket), "
            "sun protection if relevant.\n"
            "- Tie each recommendation to specific numbers from the report (e.g. POP, mm rain, °C).\n\n"
            "## Activities for the next day or so\n"
            "- Suggest indoor vs outdoor options aligned with the forecast and Nairobi’s rainy-season / "
            "flash-flood risks (avoid low-lying crossings when heavy rain is likely).\n\n"
            "If the weather block says unavailable, give cautious rainy-season defaults for Nairobi "
            "and state that advice is not tied to a live reading."
        )
    )
    human = HumanMessage(
        content=(
            f"Weather report:\n{state.get('weather_info', '')}\n\n"
            f"User question (for context): {state.get('user_question', '')}"
        )
    )
    resp = llm.invoke([system, human])
    return {"outfit_and_activities": resp.content}


def node_venues_rag(state: NairobiCityState) -> dict:
    q = state.get("user_question") or "Nairobi dining indoor activities flood safety rainy season"
    return {"venues_rag_context": retrieve_venues_context(q)}


def node_analysis(state: NairobiCityState) -> dict:
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.4)
    today = date.today()
    system = SystemMessage(
        content=(
            f"Today is **{today.isoformat()}** ({today.strftime('%A')}, {today.year}). "
            "You are a careful city guide for Nairobi, Kenya. Users may be affected by "
            "heavy rain, flooding, and traffic disruption—prioritize safety and realistic "
            "planning. Combine local/web events, weather + forecast, venue RAG notes, and the "
            "specialist outfit/activities brief. "
            "For **Events**: prioritize listings that plausibly apply to the current year "
            f"({today.year}) or near future; if sources show old years (e.g. 2023), say they "
            "may be outdated and do not present them as confirmed upcoming unless the text "
            "clearly indicates a recurring event.\n"
            "Output concise Markdown with an H1 title and these sections in order:\n"
            "1) **Events** — highlights from local/web listings\n"
            "2) **Weather snapshot** — brief summary of current + forecast\n"
            "3) **Outfit & activities** — largely reuse the specialist advice below; "
            "you may tighten wording but do not contradict the weather data\n"
            "4) **Venues & food** — use RAG context\n"
            "5) **Safety** — floods, transport, when to stay indoors\n"
            "6) **Checklist** — short bullet list\n"
            "If data is missing for a section, say so briefly."
        )
    )
    human = HumanMessage(
        content=(
            f"User question: {state.get('user_question', '')}\n\n"
            f"## Events\n{state.get('events_combined', '')}\n\n"
            f"## Weather (current + forecast)\n{state.get('weather_info', '')}\n\n"
            f"## Outfit & activities (specialist — ground recommendations in this)\n"
            f"{state.get('outfit_and_activities', '')}\n\n"
            f"## Venue RAG\n{state.get('venues_rag_context', '')}"
        )
    )
    resp = llm.invoke([system, human])
    return {"final_briefing": resp.content}


def build_graph():
    g = StateGraph(NairobiCityState)
    g.add_node("local_events", node_local_events)
    g.add_node("online_search", node_online_search)
    g.add_node("merge_local", node_merge_local)
    g.add_node("weather", node_weather)
    g.add_node("outfit_advisor", node_outfit_advisor)
    g.add_node("venues_rag", node_venues_rag)
    g.add_node("analysis", node_analysis)

    g.add_edge(START, "local_events")
    g.add_conditional_edges(
        "local_events",
        route_after_local,
        {"online_search": "online_search", "merge_local": "merge_local"},
    )
    g.add_edge("online_search", "weather")
    g.add_edge("merge_local", "weather")
    g.add_edge("weather", "outfit_advisor")
    g.add_edge("outfit_advisor", "venues_rag")
    g.add_edge("venues_rag", "analysis")
    g.add_edge("analysis", END)

    memory = MemorySaver()
    return g.compile(checkpointer=memory)


_COMPILED_APP = None


def get_compiled_app():
    global _COMPILED_APP
    if _COMPILED_APP is None:
        _COMPILED_APP = build_graph()
    return _COMPILED_APP


def run_once(user_question: str, thread_id: str) -> str:
    """Invoke the compiled graph (requires checkpointer config)."""
    app = get_compiled_app()
    initial: NairobiCityState = {
        "city": CITY,
        "user_question": user_question,
    }
    cfg: dict = {
        "configurable": {"thread_id": thread_id},
        "tags": ["nairobi-city-agents", "langgraph"],
        "metadata": {"app": "nairobi_city_agents", "city": CITY},
    }
    out = app.invoke(initial, config=cfg)
    return out.get("final_briefing") or "No output produced."
