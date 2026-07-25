from __future__ import annotations

_MAX_USER_CHARS = 12_000


def input_guardrail_stub(user_text: str) -> str | None:
    s = (user_text or "").strip()
    if not s:
        return "Please enter a message."
    if len(s) > _MAX_USER_CHARS:
        return f"Message too long (max {_MAX_USER_CHARS} characters). Try a shorter question."
    return None


def output_guardrail_stub(_tutor_text: str) -> str | None:
    return None
