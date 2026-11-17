import logging
import os

import requests

logger = logging.getLogger(__name__)
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def notify(text: str) -> None:
    user = os.getenv("PUSHOVER_USER")
    token = os.getenv("PUSHOVER_TOKEN")
    if not user or not token:
        logger.warning("Pushover notification skipped: credentials are not configured")
        return

    try:
        response = requests.post(
            PUSHOVER_URL,
            data={"user": user, "token": token, "message": text[:1024]},
            timeout=10,
        )
        if not 200 <= response.status_code < 300:
            logger.error("Pushover notification failed with status %s", response.status_code)
    except requests.RequestException as exc:
        logger.error("Pushover notification failed: %s", exc)
