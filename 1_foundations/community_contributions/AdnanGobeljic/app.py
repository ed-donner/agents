"""
Adnan Gobeljic digital twin

Loads profile context from local files and
supports function-calling if it stumbles upon an unknown question,
and applies one evaluator pass for response quality control.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from prompts import (
    build_evaluator_system_prompt,
    build_evaluator_user_prompt,
    build_rerun_extra_prompt,
    build_system_prompt,
)
from tool_jsons import TOOLS

MAX_MESSAGE_LENGTH = 2500
APP_DIR = Path(__file__).resolve().parent
DOCS_DIR = APP_DIR / "docs"
load_dotenv(APP_DIR.parent.parent.parent / ".env", override=True)


class QualityCheck(BaseModel):
    ok: bool
    feedback: str


@dataclass(slots=True)
class PersonaContext:
    name: str
    summary: str


def _read_text_file(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    content = path.read_text(encoding="utf-8").strip()
    return content or fallback


def load_persona_context() -> PersonaContext:
    return PersonaContext(
        name="Adnan Gobeljic",
        summary=_read_text_file(
            DOCS_DIR / "summary.txt",
            "(Create docs/summary.txt and add a short profile.)",
        ),
    )


def send_push_notification(message: str) -> None:
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "message": message},
            timeout=5,
        )
    except requests.RequestException:
        pass


def log_unknown_question(question: str) -> dict:
    print(f"Follow-up needed: {question}")
    send_push_notification(f"Follow-up needed: {question}")
    return {"recorded": "ok"}


TOOL_HANDLERS = {
    "log_unknown_question": log_unknown_question,
}


class MyTwin:
    def __init__(self):
        self.client = OpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.persona = load_persona_context()

    def _system_prompt(self) -> str:
        return build_system_prompt(
            self.persona.name,
            self.persona.summary,
        )

    def _evaluator_system_prompt(self) -> str:
        return build_evaluator_system_prompt(
            self.persona.name,
            self.persona.summary,
        )

    @staticmethod
    def _normalize_history(history: Any) -> list[dict[str, str]]:
        if not history:
            return []

        normalized: list[dict[str, str]] = []
        for item in history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                user_msg, assistant_msg = item
                if user_msg:
                    normalized.append({"role": "user", "content": str(user_msg)})
                if assistant_msg:
                    normalized.append({"role": "assistant", "content": str(assistant_msg)})
                continue

            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")
                if isinstance(role, str) and isinstance(content, str):
                    normalized.append({"role": role, "content": content})

        return normalized

    @staticmethod
    def _tool_results(tool_calls: Any) -> list[dict[str, str]]:
        responses = []
        for tool_call in tool_calls or []:
            fn_name = tool_call.function.name
            handler = TOOL_HANDLERS.get(fn_name)
            result: dict[str, Any] = {}

            if handler:
                try:
                    payload = json.loads(tool_call.function.arguments or "{}")
                    result = handler(**payload)
                except (json.JSONDecodeError, TypeError, ValueError):
                    result = {"recorded": "error"}

            responses.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return responses

    def _evaluate_reply(self, reply: str, message: str, history: list[dict[str, str]]) -> QualityCheck:
        history_text = "\n".join(
            f"{entry['role']}: {entry['content']}"
            for entry in history
            if isinstance(entry.get("content"), str)
        )
        evaluator_messages = [
            {"role": "system", "content": self._evaluator_system_prompt()},
            {
                "role": "user",
                "content": build_evaluator_user_prompt(history_text, message, reply),
            },
        ]
        evaluation_response = self.client.chat.completions.create(
            model=self.model,
            messages=evaluator_messages,
            temperature=0.2,
        )
        raw = (evaluation_response.choices[0].message.content or "").strip()
        json_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
        return QualityCheck.model_validate_json(json_text)

    def _rerun_with_feedback(
        self,
        reply: str,
        message: str,
        history: list[dict[str, str]],
        feedback: str,
    ) -> str:
        revised_system_prompt = self._system_prompt() + build_rerun_extra_prompt(reply, feedback)
        retry_messages = [
            {"role": "system", "content": revised_system_prompt},
            *history,
            {"role": "user", "content": message},
        ]
        retry = self.client.chat.completions.create(
            model=self.model,
            messages=retry_messages,
            temperature=0.7,
        )
        return retry.choices[0].message.content or ""

    def _generate_reply_with_tools(self, message: str, history: list[dict[str, str]]) -> str:
        messages = [
            {"role": "system", "content": self._system_prompt()},
            *history,
            {"role": "user", "content": message},
        ]
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
            )
            choice = response.choices[0]
            if choice.finish_reason != "tool_calls":
                return choice.message.content or ""

            messages.append(choice.message)
            messages.extend(self._tool_results(choice.message.tool_calls))

    def chat(self, message: Any, history: Any) -> str:
        text = str(message).strip() if message is not None else ""
        if not text:
            return "Send me a message and I'll respond."
        if len(text) > MAX_MESSAGE_LENGTH:
            return (
                f"Message too long. {MAX_MESSAGE_LENGTH} characters is the limit. "
            )

        clean_history = self._normalize_history(history)
        if not clean_history:
            send_push_notification("New chat started")
        reply = self._generate_reply_with_tools(text, clean_history)

        try:
            quality = self._evaluate_reply(reply, text, clean_history)
            if not quality.ok:
                reply = self._rerun_with_feedback(reply, text, clean_history, quality.feedback)
        except Exception as exc:
            print(f"Failed evaluator; returning first response: {exc}", flush=True)
        return reply


if __name__ == "__main__":
    runtime = MyTwin()
    gr.ChatInterface(runtime.chat).launch()
