"""
Digital twin for Olawale Adeogun.
Chat from summary + LinkedIn PDF, collect contact info, log unanswered questions.
OpenAI chat + function calling + Gradio.
"""
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

APP_DIR = Path(__file__).resolve().parent
# .env at repo root (agents/)
load_dotenv(APP_DIR.parent.parent.parent / ".env", override=True)


def push(text: str) -> None:
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if token and user:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "message": text},
            timeout=5,
        )


def record_user_details(
    email: str, name: str = "Name not provided", notes: str = "not provided"
) -> dict:
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question: str) -> dict:
    push(f"Unanswered: {question}")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional context about the conversation"},
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]


class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Olawale Adeogun"
        me_dir = APP_DIR / "me"
        self.linkedin = ""
        linkedin_path = me_dir / "linkedin.pdf"
        if linkedin_path.exists():
            reader = PdfReader(str(linkedin_path))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin += text
        else:
            self.linkedin = "(LinkedIn profile not loaded; add me/linkedin.pdf)"
        summary_path = me_dir / "summary.txt"
        if summary_path.exists():
            self.summary = summary_path.read_text(encoding="utf-8")
        else:
            self.summary = "(Add me/summary.txt with a short bio)"

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            })
        return results

    def system_prompt(self) -> str:
        prompt = (
            f"You are acting as {self.name}. You are answering questions on {self.name}'s website, "
            "particularly questions related to career, background, skills and experience. "
            f"Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. "
            "You are given a summary and LinkedIn profile which you can use to answer questions. "
            "Be professional and engaging, as if talking to a potential client or future employer. "
            "If you don't know the answer to any question, use your record_unknown_question tool to record it. "
            "If the user is engaging, steer them towards getting in touch via email and use record_user_details."
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return prompt

    def chat(self, message, history):
        # Normalize Gradio history to list of {role, content}
        if history:
            normalized = []
            for h in history:
                if isinstance(h, (list, tuple)) and len(h) == 2:
                    u, b = h
                    if u:
                        normalized.append({"role": "user", "content": u})
                    if b:
                        normalized.append({"role": "assistant", "content": b})
                elif isinstance(h, dict) and "role" in h and "content" in h:
                    normalized.append({"role": h["role"], "content": h["content"]})
            history = normalized
        messages = [
            {"role": "system", "content": self.system_prompt()},
            *history,
            {"role": "user", "content": message},
        ]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=TOOLS
            )
            if response.choices[0].finish_reason == "tool_calls":
                msg = response.choices[0].message
                results = self.handle_tool_call(msg.tool_calls)
                messages.append(msg)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
