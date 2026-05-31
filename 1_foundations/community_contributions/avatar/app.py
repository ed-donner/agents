import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader


load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PROFILE_DIR = Path(os.getenv("PROFILE_DIR", str(BASE_DIR / "me"))).resolve()
SUMMARY_PATH = PROFILE_DIR / "summary.txt"
LINKEDIN_PATH = PROFILE_DIR / "linkedin.pdf"
AGENT_NAME = os.getenv("AGENT_NAME", "Your Name")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is required in your .env file.")

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

EXTRA_HEADERS = {}
if os.getenv("OPENROUTER_SITE_URL"):
    EXTRA_HEADERS["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL")
if os.getenv("OPENROUTER_APP_NAME"):
    EXTRA_HEADERS["X-Title"] = os.getenv("OPENROUTER_APP_NAME")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    default_headers=EXTRA_HEADERS or None,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided") -> dict[str, str]:
    payload = {
        "ts": _utc_now(),
        "email": email,
        "name": name,
        "notes": notes,
    }
    _append_jsonl(DATA_DIR / "leads.jsonl", payload)
    print(f"[tool] recorded lead for {email}")
    return {"recorded": "ok", "destination": "data/leads.jsonl"}


def record_unknown_question(question: str) -> dict[str, str]:
    payload = {"ts": _utc_now(), "question": question}
    _append_jsonl(DATA_DIR / "unknown_questions.jsonl", payload)
    print("[tool] recorded unknown question")
    return {"recorded": "ok", "destination": "data/unknown_questions.jsonl"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user."},
            "name": {"type": "string", "description": "The user's name, if they provided it."},
            "notes": {
                "type": "string",
                "description": "Any additional conversation details worth recording.",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that you could not answer.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that could not be answered.",
            }
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]


def _read_profile_text() -> tuple[str, str]:
    if not LINKEDIN_PATH.exists() or not SUMMARY_PATH.exists():
        print(
            "[warning] Missing me/linkedin.pdf or me/summary.txt. "
            "Using fallback profile text; update files for best results."
        )
        return (
            "No summary was provided yet.",
            "No LinkedIn profile text was provided yet.",
        )

    reader = PdfReader(str(LINKEDIN_PATH))
    linkedin_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            linkedin_text.append(text)

    summary = SUMMARY_PATH.read_text(encoding="utf-8")
    return summary, "\n".join(linkedin_text)


summary, linkedin = _read_profile_text()

system_prompt = (
    f"You are acting as {AGENT_NAME}. You are answering questions on {AGENT_NAME}'s website, "
    f"particularly questions related to {AGENT_NAME}'s career, background, skills and experience. "
    f"Your responsibility is to represent {AGENT_NAME} as faithfully as possible. "
    "If you do not know the answer to any question, use your record_unknown_question tool to record the question. "
    "If the user is engaging in discussion, steer them towards getting in touch via email, ask for their email, "
    "and record details using record_user_details."
)
system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, chat with the user while staying in character as {AGENT_NAME}."


def _history_to_openai_messages(history: list[Any]) -> list[dict[str, str]]:
    """Gradio passes either [[user, bot], ...] (default / older) or message dicts (type='messages')."""
    if not history:
        return []
    first = history[0]
    if isinstance(first, dict) and "role" in first and "content" in first:
        return [{"role": str(h["role"]), "content": str(h["content"])} for h in history]
    out: list[dict[str, str]] = []
    for turn in history:
        if not turn:
            continue
        if isinstance(turn, (list, tuple)):
            user_msg = turn[0] if len(turn) > 0 else ""
            bot_msg = turn[1] if len(turn) > 1 else ""
            if user_msg:
                out.append({"role": "user", "content": str(user_msg)})
            if bot_msg:
                out.append({"role": "assistant", "content": str(bot_msg)})
    return out


def handle_tool_calls(tool_calls: list[Any]) -> list[dict[str, Any]]:
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"[tool-call] {tool_name}", flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {"recorded": "error", "reason": "missing tool"}
        results.append(
            {
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            }
        )
    return results


def chat(message: str, history: list[Any]) -> str:
    prior = _history_to_openai_messages(history)
    messages = [{"role": "system", "content": system_prompt}] + prior + [{"role": "user", "content": message}]

    while True:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=tools,
        )
        choice = response.choices[0]
        if choice.finish_reason == "tool_calls":
            assistant_message = choice.message
            tool_results = handle_tool_calls(assistant_message.tool_calls)
            messages.append(assistant_message)
            messages.extend(tool_results)
            continue
        return choice.message.content or ""


if __name__ == "__main__":
    gr.ChatInterface(chat).launch()
