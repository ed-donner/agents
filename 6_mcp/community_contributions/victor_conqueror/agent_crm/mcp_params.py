"""Stdio MCP server definitions for AgentCRM."""

import os
from pathlib import Path

from dotenv import load_dotenv

from paths import PACKAGE_DIR, REPO_ROOT

load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(PACKAGE_DIR / ".env", override=False)


def crm_stdio_params() -> dict:
    return {
        "command": "uv",
        "args": ["run", "python", str(PACKAGE_DIR / "crm_mcp_server.py")],
        "cwd": str(REPO_ROOT),
    }


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


def google_calendar_stdio_params() -> dict | None:
    if not _env_truthy("AGENTCRM_ENABLE_CALENDAR"):
        return None
    creds = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "").strip()
    if not creds or not Path(creds).is_file():
        return None
    env = os.environ.copy()
    env["GOOGLE_OAUTH_CREDENTIALS"] = str(Path(creds).resolve())
    filtered = os.getenv("AGENTCRM_CALENDAR_ENABLED_TOOLS", "").strip()
    if filtered:
        env["ENABLED_TOOLS"] = filtered
    return {
        "command": "npx",
        "args": ["-y", "@cocal/google-calendar-mcp"],
        "env": env,
    }


def gmail_stdio_params() -> dict | None:
    if not _env_truthy("AGENTCRM_ENABLE_GMAIL"):
        return None
    cid = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not cid or not secret:
        return None
    env = os.environ.copy()
    env["GOOGLE_CLIENT_ID"] = cid
    env["GOOGLE_CLIENT_SECRET"] = secret
    return {
        "command": "npx",
        "args": ["-y", "@mcp-z/mcp-gmail"],
        "env": env,
    }


def all_agentcrm_server_params() -> list[dict]:
    out: list[dict] = [crm_stdio_params()]
    gcal = google_calendar_stdio_params()
    if gcal:
        out.append(gcal)
    gml = gmail_stdio_params()
    if gml:
        out.append(gml)
    return out
