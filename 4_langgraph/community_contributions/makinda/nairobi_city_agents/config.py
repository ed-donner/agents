"""Nairobi multi-agent LangGraph — configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"
DB_PATH = DATA_DIR / "nairobi_events.db"
CHROMA_DIR = DATA_DIR / "chroma_venues"
VENUES_DOC = PACKAGE_ROOT / "data" / "venues_nairobi.md"

CITY = "Nairobi"
COUNTRY_CONTEXT = "Kenya"

# Smallest practical OpenAI chat model (course labs)
LLM_MODEL = os.environ.get("OPENAI_LANGGRAPH_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# LangSmith — trace LangGraph / LangChain runs (https://smith.langchain.com)
DEFAULT_LANGCHAIN_PROJECT = "nairobi-city-agents"


def configure_langsmith() -> bool:
    """Enable LangChain/LangGraph tracing for LangSmith when an API key is available.

    Set in `.env` (either key works; LangSmith UI often labels it LANGSMITH_API_KEY):
      LANGSMITH_API_KEY=<key>   → copied to LANGCHAIN_API_KEY for LangChain tracing
      LANGCHAIN_API_KEY=<key>   → used as-is
      LANGCHAIN_TRACING_V2=true  (default: enabled when a key is present; set to false to opt out)
      LANGCHAIN_PROJECT=nairobi-city-agents  (optional; groups runs in the dashboard)
    """
    project = os.environ.get("LANGCHAIN_PROJECT", DEFAULT_LANGCHAIN_PROJECT)
    os.environ.setdefault("LANGCHAIN_PROJECT", project)

    key = os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")
    if os.environ.get("LANGSMITH_API_KEY") and not os.environ.get("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]

    if not key:
        return False

    tracing = os.environ.get("LANGCHAIN_TRACING_V2", "").strip().lower()
    if tracing in ("false", "0", "no"):
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    if tracing in ("true", "1", "yes") or tracing == "":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

    return True


def langsmith_banner_markdown() -> str:
    """Short UI hint for Gradio."""
    configure_langsmith()
    project = os.environ.get("LANGCHAIN_PROJECT", DEFAULT_LANGCHAIN_PROJECT)
    has_key = bool(
        os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")
    )
    tracing_on = os.environ.get("LANGCHAIN_TRACING_V2", "true").lower() not in (
        "false",
        "0",
        "no",
    )
    if has_key and tracing_on:
        return (
            f"**LangSmith tracing is on.** Project `{project}` — "
            f"[open LangSmith](https://smith.langchain.com) to see graph steps, LLM calls, and latency."
        )
    return (
        "**LangSmith (optional):** add `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY` from "
        "[LangSmith](https://smith.langchain.com) to your `.env`. Optionally set "
        f"`LANGCHAIN_PROJECT` (default `{DEFAULT_LANGCHAIN_PROJECT}`). Set `LANGCHAIN_TRACING_V2=false` to disable."
    )


# Ensure tracing env is wired on any import of this module (before LangChain clients initialize).
configure_langsmith()
