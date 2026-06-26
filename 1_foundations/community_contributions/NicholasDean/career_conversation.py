"""Week 1 (Foundations) deliverable - a minimal "career conversation" agent.

Answers as Nicholas on his website: reads a short bio (me.md), chats with tool use, and pushes a
phone notification when a visitor leaves an email or asks something it can't answer. This is the
week-1 no-framework pattern: an LLM + tools + a tool-calling loop.

Run: uv run python career_conversation.py   (needs OPENAI_API_KEY; PUSHOVER_* optional)
"""
import json
import os
from pathlib import Path

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
openai = OpenAI()
NAME = "Nicholas Dean"
BIO = (Path(__file__).parent / "me.md").read_text(encoding="utf-8")


def push(text):                                    # phone notification (no-op if keys unset)
    if os.getenv("PUSHOVER_TOKEN"):
        requests.post("https://api.pushover.net/1/messages.json",
                      data={"token": os.getenv("PUSHOVER_TOKEN"),
                            "user": os.getenv("PUSHOVER_USER"), "message": text})


def record_user_details(email, name="anonymous", notes=""):
    push(f"{name} ({email}) got in touch. Notes: {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Couldn't answer: {question}")
    return {"recorded": "ok"}


# Tool schemas - the JSON the model sees so it knows what it's allowed to call.
TOOLS = [
    {"type": "function", "function": {
        "name": "record_user_details",
        "description": "Record a visitor's email so Nicholas can follow up",
        "parameters": {"type": "object", "required": ["email"], "additionalProperties": False,
            "properties": {"email": {"type": "string"}, "name": {"type": "string"},
                           "notes": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "record_unknown_question",
        "description": "Record any question that couldn't be answered",
        "parameters": {"type": "object", "required": ["question"], "additionalProperties": False,
            "properties": {"question": {"type": "string"}}}}},
]

SYSTEM = (
    f"You are acting as {NAME}, answering questions on his website about his career, skills and "
    f"background - professional and engaging, as if to a future employer, always in character as "
    f"{NAME}. If you don't know an answer, call record_unknown_question. If the visitor seems "
    f"interested, ask for their email and call record_user_details.\n\n## About {NAME}\n{BIO}"
)


def chat(message, history):
    messages = [{"role": "system", "content": SYSTEM}, *history, {"role": "user", "content": message}]
    while True:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=TOOLS)
        choice = response.choices[0]
        if choice.finish_reason != "tool_calls":
            return choice.message.content                  # model is done -> final answer
        messages.append(choice.message)
        for call in choice.message.tool_calls:             # model asked for a tool -> run it, loop
            result = globals()[call.function.name](**json.loads(call.function.arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})


if __name__ == "__main__":
    gr.ChatInterface(chat, type="messages", title=f"Chat with {NAME}").launch()
