"""
Digital twin for Olawale Adeogun. Docs here - https://drive.google.com/drive/folders/1VNMK1Ce7zkNPH7Q6TFnCgMDpZKNbVmdb?usp=sharing
Chat from summary + LinkedIn PDF, collect contact info, log unanswered questions.
FAQ database (SQLite) for common Q&A the model can read and write.
Quality evaluator: reject poor replies and rerun with feedback.
Input guardrails: reject empty or overly long messages.
Uses OpenRouter (or OpenAI if OpenRouter env not set). Gradio + function calling.
"""
import re
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

MAX_USER_MESSAGE_LENGTH = 2000


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

APP_DIR = Path(__file__).resolve().parent
FAQ_DB = APP_DIR / "data" / "faq.db"
load_dotenv(APP_DIR.parent.parent.parent / ".env", override=True)

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def init_faq_db():
    FAQ_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(FAQ_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                source TEXT DEFAULT 'assistant'
            )
            """
        )
        conn.commit()


def search_faq(query: str, limit: int = 5) -> dict:
    """Search FAQ by question or answer text. Returns matching rows."""
    init_faq_db()
    pattern = f"%{query.strip()}%"
    with sqlite3.connect(FAQ_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, question, answer, created_at
            FROM faq
            WHERE question LIKE ? OR answer LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (pattern, pattern, limit),
        ).fetchall()
    results = [dict(row) for row in rows]
    return {"success": True, "count": len(results), "results": results}


def add_faq(question: str, answer: str, source: str = "assistant") -> dict:
    """Add a Q&A pair to the FAQ. Use when you give a good answer worth reusing."""
    init_faq_db()
    question = question.strip()
    answer = answer.strip()
    if not question or not answer:
        return {"success": False, "message": "question and answer must be non-empty"}
    with sqlite3.connect(FAQ_DB) as conn:
        cur = conn.execute(
            "INSERT INTO faq (question, answer, source) VALUES (?, ?, ?)",
            (question, answer, source),
        )
        conn.commit()
        row_id = cur.lastrowid
    return {"success": True, "id": row_id, "message": "FAQ added"}


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

search_faq_json = {
    "name": "search_faq",
    "description": "Search the FAQ database for common questions and answers. Use when the user asks something that might already have a stored answer, or to check before answering.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search phrase (e.g. key words from the user's question)"},
            "limit": {"type": "integer", "description": "Max number of results to return", "default": 5},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

add_faq_json = {
    "name": "add_faq",
    "description": "Add a question and answer to the FAQ database. Use when you have just given a clear, reusable answer that could help for similar future questions. Do not add duplicates for the same question.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that was asked"},
            "answer": {"type": "string", "description": "The answer you gave (summary is fine)"},
        },
        "required": ["question", "answer"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": search_faq_json},
    {"type": "function", "function": add_faq_json},
]


def openai_client():
    """Use OpenRouter when OPENROUTER_API_KEY is set; otherwise default OpenAI."""
    if OPENROUTER_API_KEY:
        return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
    return OpenAI()


class Me:
    def __init__(self):
        self.openai = openai_client()
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
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
            "If the user is engaging, steer them towards getting in touch via email and use record_user_details. "
            "You have access to a FAQ database: use search_faq to look up common questions before answering when relevant; "
            "use add_faq to store a question and your answer when you have given a clear, reusable reply (avoid duplicates). "
            "If the user's message is vague or very short, you may ask one brief clarifying question before answering."
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return prompt

    def evaluator_system_prompt(self) -> str:
        prompt = (
            f"You are an evaluator that decides whether a response to a question is acceptable. "
            "You are provided with a conversation between a User and an Agent. "
            f"The Agent is playing the role of {self.name} and is representing {self.name} on their website. "
            "The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer. "
            f"Context on {self.name} (summary and LinkedIn) is below. "
            "Evaluate whether the Agent's latest response is acceptable quality: accurate, relevant, and in character."
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        prompt += "Respond with a JSON object only, with two keys: is_acceptable (boolean) and feedback (string). No other text."
        return prompt

    def evaluator_user_prompt(self, reply: str, message: str, history: list) -> str:
        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in history if isinstance(m.get("content"), str)
        )
        return (
            f"Conversation so far:\n\n{history_text}\n\n"
            f"Latest user message:\n{message}\n\n"
            f"Agent's latest response:\n{reply}\n\n"
            "Evaluate the response. Reply with JSON only: {\"is_acceptable\": true/false, \"feedback\": \"...\"}"
        )

    def evaluate(self, reply: str, message: str, history: list) -> Evaluation:
        messages = [
            {"role": "system", "content": self.evaluator_system_prompt()},
            {"role": "user", "content": self.evaluator_user_prompt(reply, message, history)},
        ]
        response = self.openai.chat.completions.create(
            model=self.model, messages=messages, temperature=0.2
        )
        raw = response.choices[0].message.content.strip()
        json_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
        return Evaluation.model_validate_json(json_str)

    def rerun(self, reply: str, message: str, history: list, feedback: str) -> str:
        extra = (
            "\n\n## Previous answer rejected\n"
            "Quality control rejected your last reply. Try again with the feedback below.\n"
            f"## Your attempted answer:\n{reply}\n\n"
            f"## Reason for rejection:\n{feedback}\n\n"
        )
        system = self.system_prompt() + extra
        messages = [
            {"role": "system", "content": system},
            *history,
            {"role": "user", "content": message},
        ]
        response = self.openai.chat.completions.create(
            model=self.model, messages=messages, temperature=0.7
        )
        return response.choices[0].message.content

    def chat(self, message, history):
        # Input guardrails
        if not message or not str(message).strip():
            return "Please type a question or message and I'll get back to you."
        msg_str = str(message).strip()
        if len(msg_str) > MAX_USER_MESSAGE_LENGTH:
            return f"Your message is too long (max {MAX_USER_MESSAGE_LENGTH} characters). Please shorten it and try again."

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
                model=self.model, messages=messages, tools=TOOLS
            )
            if response.choices[0].finish_reason == "tool_calls":
                msg = response.choices[0].message
                results = self.handle_tool_call(msg.tool_calls)
                messages.append(msg)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content

        # Evaluator: accept or rerun once with feedback
        try:
            evaluation = self.evaluate(reply, message, history)
            if not evaluation.is_acceptable:
                reply = self.rerun(reply, message, history, evaluation.feedback)
        except Exception as e:
            print(f"Evaluation failed, returning original reply: {e}", flush=True)
        return reply


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
