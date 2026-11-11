"""Week 1 capstone - "Professionally You": a deployable career-conversation agent.

Answers as Nicholas on his website. It combines the whole of week 1 with no framework:
  - tool use: record_user_details (capture an interested visitor's email) and
    record_unknown_question (log what it couldn't answer), both pushing to my phone via Pushover;
  - the tool-calling loop (call the model, run any requested tools, repeat until done);
  - an evaluator-optimizer pass: a second model grades each reply (Pydantic Evaluation), and a
    rejected reply is regenerated with the feedback before the visitor ever sees it.

Deploy to HuggingFace Spaces from this folder:  uv run gradio deploy   (entry point: app.py)
Run locally:  uv run python app.py     (needs OPENAI_API_KEY; PUSHOVER_* optional)
"""
import json
import os
from pathlib import Path

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv(override=True)
openai = OpenAI()
NAME = "Nicholas Dean"
CHAT_MODEL = "gpt-4o-mini"
EVAL_MODEL = "gpt-4o-mini"
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


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def evaluate(reply, history, message) -> Evaluation:
    """A second model grades the reply for quality + staying in character."""
    prompt = (f"You evaluate a reply from an agent acting as {NAME} on his website. Decide if it is "
              f"acceptable (professional, in character, grounded in the bio) and give feedback.\n\n"
              f"## Bio\n{BIO}\n\n## Conversation so far\n{history}\n\n## Latest user message\n{message}"
              f"\n\n## Agent reply to judge\n{reply}")
    r = openai.beta.chat.completions.parse(
        model=EVAL_MODEL,
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": "Evaluate the reply."}],
        response_format=Evaluation,
    )
    return r.choices[0].message.parsed


def generate(message, history, extra_system=""):
    messages = [{"role": "system", "content": SYSTEM + extra_system}, *history,
                {"role": "user", "content": message}]
    while True:                                       # tool-calling loop
        response = openai.chat.completions.create(model=CHAT_MODEL, messages=messages, tools=TOOLS)
        choice = response.choices[0]
        if choice.finish_reason != "tool_calls":
            return choice.message.content
        messages.append(choice.message)
        for call in choice.message.tool_calls:
            result = globals()[call.function.name](**json.loads(call.function.arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})


def chat(message, history):
    reply = generate(message, history)
    evaluation = evaluate(reply, history, message)
    if not evaluation.is_acceptable:                  # optimizer: retry once with the feedback
        retry = (f"\n\n## A previous attempt was rejected by quality control\nFeedback: "
                 f"{evaluation.feedback}\nRewrite the reply addressing this.")
        reply = generate(message, history, extra_system=retry)
    return reply


if __name__ == "__main__":
    gr.ChatInterface(chat, type="messages", title=f"Chat with {NAME}").launch()
