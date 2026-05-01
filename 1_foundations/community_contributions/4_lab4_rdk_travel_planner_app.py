from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import gradio as gr

load_dotenv(override=True)

openai = OpenAI()

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

if pushover_user:
    print(f"Pushover user found and starts with {pushover_user[0]}")
else:
    print("Pushover user not found")

if pushover_token:
    print(f"Pushover token found and starts with {pushover_token[0]}")
else:
    print("Pushover token not found")


def push(message):
    print(f"Push: {message}")
    if pushover_user and pushover_token:
        try:
            payload = {"user": pushover_user, "token": pushover_token, "message": message}
            resp = requests.post(pushover_url, data=payload, timeout=5)
            if resp.ok:
                print("Pushover: sent")
            else:
                print(f"Pushover: failed {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Pushover error: {e}")
    else:
        print("Pushover not configured; skipping external request.")


def generate_itinerary(destination, duration_days=3, interests="general"):
    prompt = f"Create a {duration_days}-day travel itinerary for {destination}. Mix touristy and offbeat places. Include tips to avoid crowds. Interests: {interests}."
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    itinerary = response.choices[0].message.content
    push(f"Generated itinerary for {destination}")
    return {"itinerary": itinerary}


def record_feedback(feedback):
    push(f"User feedback: {feedback}")
    return {"recorded": "ok"}


generate_itinerary_json = {
    "name": "generate_itinerary",
    "description": "Generate a travel itinerary mixing offbeat and touristy places with crowd-avoidance tips",
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {"type": "string", "description": "The travel destination"},
            "duration_days": {"type": "integer", "description": "Number of days", "default": 3},
            "interests": {"type": "string", "description": "User interests"}
        },
        "required": ["destination"]
    }
}

record_feedback_json = {
    "name": "record_feedback",
    "description": "Record user feedback or questions about the itinerary",
    "parameters": {
        "type": "object",
        "properties": {
            "feedback": {"type": "string", "description": "The feedback or question"}
        },
        "required": ["feedback"]
    }
}

tools = [{"type": "function", "function": generate_itinerary_json},
         {"type": "function", "function": record_feedback_json}]

system_prompt = (
    "You are a helpful travel itinerary planner. Create itineraries that mix popular tourist spots with offbeat, "
    "hidden gems. Always include practical tips to avoid crowds, like visiting early or off-season. "
    "If the user asks for an itinerary, use the generate_itinerary tool. "
    "If they provide feedback or ask something unknown, use record_feedback. Be engaging and suggest contacting for more details."
)


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
    return results


def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    done = False
    while not done:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            done = True
    return response.choices[0].message.content


if __name__ == "__main__":
    gr.ChatInterface(chat).launch(pwa=True, share=False)
