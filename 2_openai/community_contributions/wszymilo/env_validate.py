"""Required environment variables for v1 - no opt-out (plan.md Phase B)."""

from __future__ import annotations

import os

REQUIRED_ENV_VARS = (
    "OPENAI_API_KEY",
    "SERPER_API_KEY",
    "PUSHOVER_TOKEN",
    "PUSHOVER_USER",
)


def list_missing_required_env() -> list[str]:
    return [k for k in REQUIRED_ENV_VARS if not os.getenv(k)]


def format_env_error(missing: list[str]) -> str:
    return (
        "**Configuration error:** missing required environment variables: **"
        + "**, **".join(missing)
        + "**. Set them in the process environment or in a discoverable `.env` "
        "(loaded via `config` / `find_dotenv`; see `plan.md`)."
    )
