"""Pushover notification after evaluator approval (plan.md Phase H)."""

from __future__ import annotations

import os

import requests

import config

PUSHOVER_MESSAGES_URL = "https://api.pushover.net/1/messages.json"
MAX_MESSAGE_CHARS = 300


def truncate_pushover_message(text: str) -> str:
    """Hard-truncate to ``MAX_MESSAGE_CHARS`` (plan.md Phase H)."""
    t = (text or "").strip()
    if len(t) <= MAX_MESSAGE_CHARS:
        return t
    return t[:MAX_MESSAGE_CHARS]


def send_pushover_completion_notice(
    *,
    message: str | None = None,
    token: str | None = None,
    user: str | None = None,
    timeout: float = 30.0,
) -> tuple[bool, str]:
    """POST to Pushover; success only if HTTP OK and JSON ``status == 1``."""
    tok = (token if token is not None else os.getenv("PUSHOVER_TOKEN") or "").strip()
    usr = (user if user is not None else os.getenv("PUSHOVER_USER") or "").strip()
    if not tok or not usr:
        return False, "Missing PUSHOVER_TOKEN or PUSHOVER_USER"

    body = truncate_pushover_message(message or config.PUSHOVER_NOTIFY_MESSAGE)

    try:
        r = requests.post(
            PUSHOVER_MESSAGES_URL,
            data={"token": tok, "user": usr, "message": body},
            timeout=timeout,
        )
        r.raise_for_status()
    except requests.RequestException as exc:
        return False, str(exc)

    try:
        data = r.json()
    except ValueError:
        return False, "Pushover response was not valid JSON"

    if data.get("status") != 1:
        errs = data.get("errors")
        detail = f"errors={errs!r}" if errs else repr(data)
        return False, f"Pushover API did not return status=1 ({detail})"

    return True, ""
