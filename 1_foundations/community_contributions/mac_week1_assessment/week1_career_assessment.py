"""
Week 1 assessment — extended career chatbot (Labs 3–4 + exercise).

- Tool-calling agent loop (4_lab4)
- SQLite FAQ the agent can query before improvising (4_lab4 exercise)
- LLM-as-judge with one retry on failure (3_lab3)
- Optional Pushover notifications

Run from repo root:
  uv run python 1_foundations/community_contributions/mac_week1_assessment/week1_career_assessment.py

Requires `me/linkedin.pdf` and `me/summary.txt` under `1_foundations/me/` (course default).
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader

load_dotenv(override=True)

MODEL = "gpt-4o-mini"
FAQ_DB_NAME = "faq_assessment.db"
MAX_EVAL_RETRIES = 1


def _find_me_dir() -> Path:
    here = Path(__file__).resolve().parent
    for base in [here, *here.parents]:
        candidate = base / "me"
        if candidate.is_dir() and (candidate / "summary.txt").is_file():
            return candidate
        # contribution folder: ../../me from 1_foundations/community_contributions/x/
        alt = base.parent / "me"
        if alt.is_dir() and (alt / "summary.txt").is_file():
            return alt
    raise FileNotFoundError(
        "Could not find 1_foundations/me with summary.txt — place your profile files there."
    )


def _faq_db_path() -> Path:
    return Path(__file__).resolve().parent / FAQ_DB_NAME


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str = Field(default="")


def push(text: str) -> None:
    user, token = os.getenv("PUSHOVER_USER"), os.getenv("PUSHOVER_TOKEN")
    if not user or not token:
        print(f"[push skipped] {text}")
        return
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={"user": user, "token": token, "message": text},
        timeout=30,
    )


class FAQStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL
                )
                """
            )
            cur = conn.execute("SELECT COUNT(*) FROM faq")
            if cur.fetchone()[0] == 0:
                seed = [
                    (
                        "What stack do you use?",
                        "Python for agents and backends, OpenAI APIs, and Gradio for quick UIs — see my summary and LinkedIn for more.",
                    ),
                    (
                        "Are you open to consulting?",
                        "Yes — use the chat to leave your email and a short note, and I will follow up.",
                    ),
                ]
                conn.executemany(
                    "INSERT INTO faq (question, answer) VALUES (?, ?)", seed
                )
                conn.commit()

    def all_pairs(self) -> list[tuple[str, str]]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT question, answer FROM faq ORDER BY id"
            ).fetchall()
        return [(str(q), str(a)) for q, a in rows]

    def add_pair(self, question: str, answer: str) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO faq (question, answer) VALUES (?, ?)", (question, answer)
            )
            conn.commit()


def match_faq_with_llm(
    client: OpenAI, user_question: str, pairs: list[tuple[str, str]]
) -> tuple[str | None, bool]:
    if not pairs:
        return None, False
    lines = "\n".join(f"Q{i+1}: {q}\nA{i+1}: {a}" for i, (q, a) in enumerate(pairs))
    prompt = f"""You have a list of canonical FAQ entries. The user asked:
"{user_question}"

FAQ entries:
{lines}

If one entry clearly answers the user, reply with JSON only: {{"use_index": <1-based index>, "answer": "<verbatim or lightly edited answer from that entry>"}}
If none fit, reply with: {{"use_index": 0, "answer": ""}}"""
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    raw = r.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, False
    idx = int(data.get("use_index", 0))
    ans = (data.get("answer") or "").strip()
    if idx < 1 or not ans:
        return None, False
    return ans, True


class CareerBot:
    def __init__(self) -> None:
        self.me_dir = _find_me_dir()
        self.openai = OpenAI()
        self.name = "Course Student"  # personalize when you deploy
        reader = PdfReader(str(self.me_dir / "linkedin.pdf"))
        self.linkedin = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                self.linkedin += t
        self.summary = (self.me_dir / "summary.txt").read_text(encoding="utf-8")
        self.faq = FAQStore(_faq_db_path())
        self._build_tool_specs()
        self._eval_system: str | None = None

    def _build_tool_specs(self) -> None:
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "record_user_details",
                    "description": "Record that a user wants to stay in touch and gave an email.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "name": {
                                "type": "string",
                                "description": "User name if provided",
                            },
                            "notes": {
                                "type": "string",
                                "description": "Extra context from the chat",
                            },
                        },
                        "required": ["email"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "record_unknown_question",
                    "description": "Record a question you could not answer from the profile or FAQ.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                        },
                        "required": ["question"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_faq",
                    "description": "Search the curated FAQ database for a matching answer before guessing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_question": {
                                "type": "string",
                                "description": "The user's question in their own words",
                            },
                        },
                        "required": ["user_question"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def system_prompt(self) -> str:
        sp = (
            f"You are acting as {self.name}. You answer questions on {self.name}'s site "
            f"about career, skills, and background. Use the summary and LinkedIn context. "
            f"Be professional and engaging. "
            f"When a question might match a common FAQ, call lookup_faq first. "
            f"If you cannot answer from context, call record_unknown_question. "
            f"When the user shares interest or an email, use record_user_details."
        )
        sp += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn:\n{self.linkedin}\n"
        return sp

    def evaluator_system_prompt(self) -> str:
        if self._eval_system is None:
            self._eval_system = (
                f"You evaluate whether the Agent's latest reply is acceptable. "
                f"The Agent represents {self.name} on their website; replies should be "
                f"professional, on-topic, and consistent with the profile below.\n\n"
                f"## Summary:\n{self.summary}\n\n## LinkedIn:\n{self.linkedin}\n"
            )
        return self._eval_system

    def dispatch_tool(self, name: str, args: dict) -> dict:
        if name == "record_user_details":
            push(
                f"Lead: {args.get('name', '')} <{args['email']}> — {args.get('notes', '')}"
            )
            return {"recorded": "ok"}
        if name == "record_unknown_question":
            push(f"Unknown Q: {args['question']}")
            return {"recorded": "ok"}
        if name == "lookup_faq":
            pairs = self.faq.all_pairs()
            answer, found = match_faq_with_llm(
                self.openai, args["user_question"], pairs
            )
            return {"found": found, "answer": answer or ""}
        return {}

    def handle_tool_calls(self, tool_calls) -> list[dict]:
        out = []
        for tc in tool_calls:
            fn = tc.function.name
            raw_args = tc.function.arguments or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                arguments = {}
            print(f"Tool: {fn}", flush=True)
            result = self.dispatch_tool(fn, arguments)
            out.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tc.id,
                }
            )
        return out

    def run_agent_loop(self, messages: list) -> str:
        done = False
        response = None
        while not done:
            response = self.openai.chat.completions.create(
                model=MODEL, messages=messages, tools=self.tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                msg = response.choices[0].message
                results = self.handle_tool_calls(msg.tool_calls)
                messages.append(msg)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content or ""

    def evaluate(self, reply: str, message: str, history: list) -> Evaluation:
        hist = json.dumps(history[-6:], ensure_ascii=False)
        user = (
            f"Conversation (truncated):\n{hist}\n\n"
            f"Latest user message:\n{message}\n\n"
            f"Agent reply:\n{reply}\n\n"
            f"Return structured evaluation: acceptable or not, with short feedback."
        )
        r = self.openai.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": self.evaluator_system_prompt()},
                {"role": "user", "content": user},
            ],
            response_format=Evaluation,
        )
        parsed = r.choices[0].message.parsed
        assert parsed is not None
        return parsed

    def rerun(self, reply: str, message: str, history: list, feedback: str) -> str:
        extra = (
            f"\n\n## Quality check failed\nYour previous answer was rejected.\n"
            f"Attempted answer:\n{reply}\n\nFeedback:\n{feedback}\n"
            f"Reply again, staying in character."
        )
        messages = (
            [{"role": "system", "content": self.system_prompt() + extra}]
            + history
            + [{"role": "user", "content": message}]
        )
        return self.run_agent_loop(messages)

    def chat(self, message: str, history: list) -> str:
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        messages = (
            [{"role": "system", "content": self.system_prompt()}]
            + history
            + [{"role": "user", "content": message}]
        )
        reply = self.run_agent_loop(messages)
        ev = self.evaluate(reply, message, history)
        retries = 0
        while not ev.is_acceptable and retries < MAX_EVAL_RETRIES:
            print(f"Evaluator retry {retries + 1}: {ev.feedback}", flush=True)
            reply = self.rerun(reply, message, history, ev.feedback)
            ev = self.evaluate(reply, message, history)
            retries += 1
        return reply


def main() -> None:
    bot = CareerBot()
    gr.ChatInterface(bot.chat, type="messages").launch()


if __name__ == "__main__":
    main()
