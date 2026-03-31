from __future__ import annotations

import logging

from asket_mcp.config import get_settings

logger = logging.getLogger(__name__)

_COACH_SYSTEM = """You are a concise, friendly study coach for a learner using Personal Study Brain.
You ground answers in the CONTEXT passages when present; if context is insufficient, say so briefly and suggest what to ingest or read.
Use short paragraphs or bullets. No medical or legal claims beyond general study advice."""

_GREET_SYSTEM = """You are welcoming a learner to Personal Study Brain. In 3–5 short bullet points:
- Acknowledge their stated goals and level (if any).
- Suggest one concrete next step for this week.
- Mention they can ingest readings into semantic memory and use ask_the_brain for questions.
Stay under 180 words."""


def _client():
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("openai package required. Install: uv sync --extra semantic") from e
    key = (get_settings().openai_api_key or "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=key)


def ask_the_brain(question: str, context_block: str) -> str:
    q = (question or "").strip()
    if not q:
        return "Ask a non-empty question."
    ctx = (context_block or "").strip() or "No local context retrieved."
    client = _client()
    model = get_settings().chat_model
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,
        max_tokens=1200,
        messages=[
            {"role": "system", "content": _COACH_SYSTEM},
            {
                "role": "user",
                "content": f"CONTEXT (from learner's local semantic memory):\n{ctx}\n\nQUESTION:\n{q}",
            },
        ],
    )
    choice = resp.choices[0].message.content
    return (choice or "").strip() or "(empty model reply)"


def greet_and_assess(profile_goals: str, profile_expertise: str, profile_roadmap: str) -> str:
    client = _client()
    model = get_settings().chat_model
    blob = (
        f"Goals: {profile_goals or '(not set)'}\n"
        f"Expertise: {profile_expertise or '(not set)'}\n"
        f"Roadmap notes: {(profile_roadmap or '(not set)')[:2000]}"
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0.5,
        max_tokens=500,
        messages=[
            {"role": "system", "content": _GREET_SYSTEM},
            {"role": "user", "content": blob},
        ],
    )
    choice = resp.choices[0].message.content
    return (choice or "").strip() or "(empty model reply)"
