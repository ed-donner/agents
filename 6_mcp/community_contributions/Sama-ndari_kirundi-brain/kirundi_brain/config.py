"""Environment-backed settings for the Kirundi Brain MCP server."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional until deps installed
    load_dotenv = None

_CONTRIB_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_BRAIN = _CONTRIB_ROOT / "brain"
_DEFAULT_DATA = _CONTRIB_ROOT / "data"

if load_dotenv is not None:
    load_dotenv(_CONTRIB_ROOT / ".env", override=False)


def brain_root() -> Path:
    """Return the allow-listed Markdown corpus directory."""
    raw = (os.getenv("KIRUNDI_BRAIN_DIR") or "").strip()
    root = Path(raw).expanduser().resolve() if raw else _DEFAULT_BRAIN.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def data_dir() -> Path:
    """Return the local data directory (SQLite profile, etc.)."""
    raw = (os.getenv("KIRUNDI_BRAIN_DATA_DIR") or "").strip()
    path = Path(raw).expanduser().resolve() if raw else _DEFAULT_DATA.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def openai_api_key() -> str | None:
    """Return OPENAI_API_KEY if set."""
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return key or None


def openai_model() -> str:
    """Return chat model id for ask_kirundi."""
    return (os.getenv("KIRUNDI_BRAIN_MODEL") or "gpt-4o-mini").strip()
