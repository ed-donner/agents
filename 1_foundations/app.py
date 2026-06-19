from dotenv import load_dotenv
from openai import OpenAI
import json
import os
from pathlib import Path
import requests
from pypdf import PdfReader
import gradio as gr


_REPO_ROOT = Path(__file__).resolve().parent.parent
_FOUNDATIONS = Path(__file__).resolve().parent
# Course .env lives in project root (`agents/`); cwd may be `1_foundations/` when you run app.py.
# override=False so Hugging Face Space secrets (env vars) are not replaced by a missing/empty .env.
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_FOUNDATIONS / ".env")
load_dotenv()

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _openai_client() -> OpenAI:
    """OpenRouter keys go in OPENAI_API_KEY; base URL defaults to OpenRouter for sk-or-* keys."""
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "Missing OPENAI_API_KEY. Locally: add it to agents/.env. "
            "On Hugging Face: Space → Settings (gear) → Variables and secrets → add Repository secret "
            "named exactly OPENAI_API_KEY. OpenRouter keys (sk-or-...) work; optional OPENAI_BASE_URL."
        )
    base = os.getenv("OPENAI_BASE_URL")
    if not base and key.startswith("sk-or-"):
        base = _OPENROUTER_BASE
    return OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)


def _me_profile_pdf() -> Path:
    """Prefer LinkedIn export as Profile.pdf; fall back to linkedin.pdf (course default)."""
    me = _FOUNDATIONS / "me"
    for fname in ("Profile.pdf", "linkedin.pdf"):
        p = me / fname
        if p.is_file():
            return p
    raise FileNotFoundError(
        "Add me/Profile.pdf (LinkedIn Save to PDF) or me/linkedin.pdf to run the twin."
    )

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = _openai_client()
        self.name = "Iduma Chika"
        reader = PdfReader(str(_me_profile_pdf()))
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open(_FOUNDATIONS / "me" / "summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    