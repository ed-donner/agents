"""
OpenAI Agents SDK + MCPServerStdio, same pattern as Week 6 Lab 1.

LLM traffic uses OpenRouter only (OpenAI-compatible API).

Usage (from this directory, with deps installed):
  export OPENROUTER_API_KEY=...
  export OPENROUTER_MODEL=openai/gpt-4o-mini   # optional
  export REPO_ONBOARDING_ROOT=/path/to/repo   # optional; defaults to course repo root
  uv run agent_demo.py "What is the layout of this codebase?"
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

OPENROUTER_DEFAULT_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-4o-mini"

_CONTRIB = Path(__file__).resolve().parent
# Default: repo_onboarding_mcp -> community_contributions -> 6_mcp -> agents/
_DEFAULT_REPO = str(_CONTRIB.parent.parent.parent)


INSTRUCTIONS = """
You help a new contributor understand a local codebase. You only know what you get from your tools:
list_repo_directory, read_repo_file, search_repo_text, summarize_repo.

Rules:
- Use tools to verify paths; do not invent filenames.
- Prefer README, pyproject.toml, package.json, or docs when orienting.
- Give a concise answer: architecture sketch, how to run/tests if found, and where to change code for a typical task.
- If something is unknown from the repo, say so.
"""


def build_model() -> Any:
    """OpenRouter via OpenAI-compatible client (see https://openrouter.ai/)."""
    router_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not router_key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY in the environment (https://openrouter.ai/keys)."
        )
    base = (os.getenv("OPENROUTER_BASE_URL") or OPENROUTER_DEFAULT_BASE).strip()
    model = (os.getenv("OPENROUTER_MODEL") or OPENROUTER_DEFAULT_MODEL).strip()
    headers: dict[str, str] = {}
    ref = (os.getenv("OPENROUTER_HTTP_REFERER") or "").strip()
    if ref:
        headers["HTTP-Referer"] = ref
    title = (os.getenv("OPENROUTER_APP_TITLE") or "").strip()
    if title:
        headers["X-Title"] = title
    client_kwargs: dict[str, Any] = {"base_url": base, "api_key": router_key}
    if headers:
        client_kwargs["default_headers"] = headers
    client = AsyncOpenAI(**client_kwargs)
    return OpenAIChatCompletionsModel(model=model, openai_client=client)


def model_label() -> str:
    return f"OpenRouter / {(os.getenv('OPENROUTER_MODEL') or '').strip() or OPENROUTER_DEFAULT_MODEL}"


async def run_agent(user_query: str, repo_root: str | None = None) -> str:
    root = (repo_root or os.environ.get("REPO_ONBOARDING_ROOT") or _DEFAULT_REPO).strip()
    env = {**os.environ, "REPO_ONBOARDING_ROOT": root}

    mcp_params: dict = {
        "command": sys.executable,
        "args": [str(_CONTRIB / "server.py")],
        "cwd": str(_CONTRIB),
        "env": env,
    }

    async with MCPServerStdio(
        params=mcp_params,
        client_session_timeout_seconds=120,
    ) as mcp:
        with trace("repo_onboarding_mcp"):
            agent = Agent(
                name="repo_onboarding",
                instructions=INSTRUCTIONS,
                model=build_model(),
                mcp_servers=[mcp],
            )
            result = await Runner.run(agent, user_query)
            return result.final_output


def main() -> None:
    if not (os.getenv("OPENROUTER_API_KEY") or "").strip():
        print("Error: set OPENROUTER_API_KEY (https://openrouter.ai/keys).", file=sys.stderr)
        sys.exit(1)
    query = " ".join(sys.argv[1:]).strip() or (
        "Summarize this repository for a new developer: main areas, how to run or test if documented, "
        "and one good first file to read."
    )
    repo = os.environ.get("REPO_ONBOARDING_ROOT", _DEFAULT_REPO)
    print(f"{model_label()}\nREPO_ONBOARDING_ROOT={repo}\n", file=sys.stderr)
    out = asyncio.run(run_agent(query, repo_root=repo))
    print(out)


if __name__ == "__main__":
    main()
