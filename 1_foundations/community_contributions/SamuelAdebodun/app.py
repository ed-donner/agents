"""
Site assistant for Samuel T. Adebodun (samueladebodun.com).

Setup:
- Copy `.env` from 1_foundations (or create one) with OPENAI_API_KEY, PUSHOVER_USER, PUSHOVER_TOKEN.
- Optional: add `me/linkedin.pdf` (export from LinkedIn) for richer answers; `me/summary.txt` is always loaded.

Run from this folder: python app.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

_BASE = Path(__file__).resolve().parent
_ME = _BASE / "me"

load_dotenv(override=True)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def push(text: str) -> None:
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print("Pushover: PUSHOVER_TOKEN or PUSHOVER_USER missing; skipping notification.", flush=True)
        return
    requests.post(
        PUSHOVER_URL,
        data={"token": token, "user": user, "message": text},
        timeout=30,
    )


def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided"):
    push(f"[Site chat] {name} — {email}. Notes: {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question: str):
    push(f"[Site chat] Unanswered question: {question}")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user",
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it",
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation worth recording for context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question you could not answer from the provided context about Samuel",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The full question that could not be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]


def _read_pdf_text(path: Path) -> str:
    if not path.is_file():
        return ""
    out = []
    reader = PdfReader(str(path))
    for page in reader.pages:
        text = page.extract_text()
        if text:
            out.append(text)
    return "\n".join(out)


class SiteAssistant:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Samuel T. Adebodun"
        self.site_url = "https://www.samueladebodun.com/"
        pdf_path = _ME / "linkedin.pdf"
        self.linkedin = _read_pdf_text(pdf_path)
        if not self.linkedin:
            print(
                "Optional: add me/linkedin.pdf for richer answers (export from LinkedIn).",
                flush=True,
            )
        summary_path = _ME / "summary.txt"
        self.summary = summary_path.read_text(encoding="utf-8") if summary_path.is_file() else ""

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            fn = globals().get(tool_name)
            result = fn(**arguments) if fn else {}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def system_prompt(self) -> str:
        return f"""You are acting as {self.name}. You answer questions for visitors who found {self.name} via \
{self.site_url}—especially career, cloud/DevOps work, skills, projects, and blog topics.

Represent {self.name} faithfully from the context below. Be professional and approachable (potential clients, employers, or readers).

Rules:
- Answer only from the summary and LinkedIn text below, plus general public knowledge that does not contradict them.
- If you cannot answer from that context, call `record_unknown_question` with the user's exact question, then reply briefly that you do not have that detail handy and suggest they reach out (e.g. via the site's contact paths) without inventing facts.
- When someone wants to connect or discuss work, ask for their email and use `record_user_details` once they provide it.

## Summary
{self.summary}

## LinkedIn export (PDF text)
{self.linkedin or "(Not provided—add me/linkedin.pdf for fuller context.)"}

Stay in character as {self.name}."""

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
            if response.choices[0].finish_reason == "tool_calls":
                msg = response.choices[0].message
                tool_calls = msg.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(msg)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


if __name__ == "__main__":
    assistant = SiteAssistant()
    gr.ChatInterface(assistant.chat, type="messages", title=f"{assistant.name} — site assistant").launch()
