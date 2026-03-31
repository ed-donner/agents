from __future__ import annotations

import logging

import httpx

from asket_mcp.config import get_settings

logger = logging.getLogger(__name__)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


class PushoverConfigError(RuntimeError):
    pass


class PushoverRequestError(RuntimeError):
    pass


def send_message(message: str) -> str:
    settings = get_settings()
    if not settings.pushover_user or not settings.pushover_token:
        raise PushoverConfigError(
            "Set PUSHOVER_USER and PUSHOVER_TOKEN in the environment or .env file."
        )
    payload = {
        "user": settings.pushover_user,
        "token": settings.pushover_token,
        "message": message.strip()[:1024],
    }
    timeout = httpx.Timeout(settings.httpx_timeout_seconds)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(PUSHOVER_URL, data=payload)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("Pushover HTTP %s: %s", e.response.status_code, e.response.text[:500])
        raise PushoverRequestError(f"Pushover request failed: {e.response.status_code}") from e
    body = response.json()
    if body.get("status") != 1:
        raise PushoverRequestError(f"Pushover rejected the message: {body!r}")
    logger.info("Pushover notification accepted")
    return "Push notification sent."
