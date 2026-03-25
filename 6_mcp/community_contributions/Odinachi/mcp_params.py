
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

_DIR = Path(__file__).resolve().parent
# Odinachi -> community_contributions -> 6_mcp -> repo root (agents/)
_REPO_ROOT = _DIR.parents[3]


def health_triage_mcp_params() -> dict:
    script = _DIR / "health_triage_server.py"
    # Use the same interpreter as the parent app (Chainlit / CLI) so `mcp` and deps match
    # the repo venv. `uv run python …` can spawn an environment without `mcp`.
    return {
        "command": sys.executable,
        "args": [str(script)],
        "cwd": str(_REPO_ROOT),
    }


def health_web_research_mcp_params(session_stem: str = "odinachi_health") -> list[dict]:
    """
    Fetch (always) + optional Brave Search + libsql memory for the research sub-agent.
    Set BRAVE_API_KEY for web search; without it, only fetch is available.
    """
    memory_dir = _DIR / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    libsql_url = f"file:{memory_dir / session_stem}.db"
    servers: list[dict] = [
        {
            "command": "uvx",
            "args": ["mcp-server-fetch"],
            "cwd": str(_REPO_ROOT),
        }
    ]
    brave = os.getenv("BRAVE_API_KEY")
    if brave:
        servers.append(
            {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": brave},
                "cwd": str(_REPO_ROOT),
            }
        )
    servers.append(
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": libsql_url},
            "cwd": str(_REPO_ROOT),
        }
    )
    return servers
