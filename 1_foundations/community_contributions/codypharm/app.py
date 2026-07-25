"""
Codypharm career chatbot – Gradio app for Hugging Face Spaces.
Set OPENAI_API_KEY (and optionally PUSHOVER_USER, PUSHOVER_TOKEN) in Space Secrets.
"""
import json
import os
import sqlite3
import requests
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)
openai = OpenAI()

# Paths relative to this script (works when run from HF Spaces or locally)
BASE = Path(__file__).resolve().parent
LINKEDIN_PDF = BASE / "linkedin.pdf"
SUMMARY_TXT = BASE / "summary.txt"
QA_DB_PATH = BASE / "qa.db"

# --- Pushover (optional: no-op if credentials missing) ---
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


def push(message: str) -> None:
    if pushover_user and pushover_token:
        requests.post(pushover_url, data={"user": pushover_user, "token": pushover_token, "message": message})
    else:
        print(f"Push (no creds): {message}")


def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question: str):
    push(f"Recording question I couldn't answer: {question}")
    return {"recorded": "ok"}


# --- SQLite Q&A ---
def _init_qa_db():
    conn = sqlite3.connect(QA_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


_init_qa_db()


def query_qa(question: str | None = None):
    conn = sqlite3.connect(QA_DB_PATH)
    conn.row_factory = sqlite3.Row
    if question and question.strip():
        cur = conn.execute(
            "SELECT question, answer FROM qa WHERE question LIKE ? OR answer LIKE ? ORDER BY id DESC LIMIT 10",
            (f"%{question.strip()}%", f"%{question.strip()}%"),
        )
    else:
        cur = conn.execute("SELECT question, answer FROM qa ORDER BY id DESC LIMIT 20")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "pairs": rows}


def upsert_qa(question: str, answer: str):
    conn = sqlite3.connect(QA_DB_PATH)
    conn.execute("INSERT INTO qa (question, answer) VALUES (?, ?)", (question.strip(), answer.strip()))
    conn.commit()
    conn.close()
    return {"recorded": "ok"}


# --- Tool definitions ---
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional context worth recording"},
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered.",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "The question that couldn't be answered"}},
        "required": ["question"],
        "additionalProperties": False,
    },
}

query_qa_json = {
    "name": "query_qa",
    "description": "Look up stored Q&A pairs. Pass a search string or omit to get recent pairs.",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "Optional search string to filter Q&A."}},
        "required": [],
        "additionalProperties": False,
    },
}

upsert_qa_json = {
    "name": "upsert_qa",
    "description": "Store a new Q&A pair for future use (e.g. contact preference, availability).",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question or topic."},
            "answer": {"type": "string", "description": "The answer to store."},
        },
        "required": ["question", "answer"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": query_qa_json},
    {"type": "function", "function": upsert_qa_json},
]

TOOL_MAP = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
    "query_qa": query_qa,
    "upsert_qa": upsert_qa,
}


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool = TOOL_MAP.get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
    return results


# --- Load context ---
reader = PdfReader(LINKEDIN_PDF)
linkedin = "".join(page.extract_text() or "" for page in reader.pages)
summary = SUMMARY_TXT.read_text(encoding="utf-8")
name = "Codypharm"

system_prompt = (
    f"You are acting as {name}. You are answering questions on {name}'s website, "
    "particularly about career, background, skills and experience. "
    "Represent {name} faithfully. Use the summary and LinkedIn context to answer. "
    "Be professional and engaging. "
    "If you don't know the answer, use record_unknown_question. "
    "If the user wants to stay in touch, ask for their email and use record_user_details. "
    "Use query_qa to look up stored Q&A; use upsert_qa to store new Q&A when the user shares something worth remembering. "
)
system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\nWith this context, chat in character as {name}."


# --- Evaluator ---
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


evaluator_system_prompt = (
    f"You are an evaluator. The Agent is playing the role of {name}. "
    "Decide if the Agent's latest response is acceptable (accurate, on-topic, professional). "
    "Reply with is_acceptable (true/false) and brief feedback."
)
evaluator_system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn (excerpt):\n{linkedin[:4000]}..."


def evaluator_user_prompt(reply: str, message: str, history: list) -> str:
    conv = "\n".join(f"{h.get('role', 'user')}: {(h.get('content') or '')[:200]}" for h in history) if history else "(no prior messages)"
    return f"Conversation:\n{conv}\n\nUser's latest: {message}\n\nAgent's response: {reply}\n\nEvaluate: is this acceptable and in character?"


def evaluate(reply: str, message: str, history: list) -> Evaluation:
    messages = [
        {"role": "system", "content": evaluator_system_prompt},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = openai.beta.chat.completions.parse(model="gpt-4o-mini", messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed


def rerun(reply: str, message: str, history: list, feedback: str) -> str:
    updated_system = (
        system_prompt
        + "\n\n[Previous reply rejected.]\n"
        + f"Your attempt: {reply[:500]}...\nFeedback: {feedback}\nReply again addressing the feedback."
    )
    messages = [{"role": "system", "content": updated_system}] + history + [{"role": "user", "content": message}]
    return openai.chat.completions.create(model="gpt-4o-mini", messages=messages).choices[0].message.content


def chat(message, history):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    done = False
    while not done:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
            msg = response.choices[0].message
            results = handle_tool_calls(msg.tool_calls)
            messages.append(msg)
            messages.extend(results)
        else:
            done = True
    reply = response.choices[0].message.content
    evaluation = evaluate(reply, message, history)
    if not evaluation.is_acceptable:
        reply = rerun(reply, message, history, evaluation.feedback)
    return reply


# --- Gradio ---
demo = gr.ChatInterface(chat, type="messages", title="Codypharm – Career chatbot")
demo.launch()
