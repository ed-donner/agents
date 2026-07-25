"""Optional OpenAI Agents SDK demo wiring MCPServerStdio to the timezone server."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

HERE = Path(__file__).resolve().parent

OPENROUTER_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

INSTRUCTIONS = """
You help with timezones using MCP tools only:
- search_timezones(prefix): find IANA zone names
- now_in_zone(timezone): current local time and offset
- utc_to_zone(utc_iso, timezone): convert a UTC instant to a zone

Keep answers short. Use ISO-8601 dates. If a zone is unknown, call search_timezones first.
"""


def _openrouter_client() -> AsyncOpenAI:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    return AsyncOpenAI(
        base_url=OPENROUTER_BASE,
        api_key=key,
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost"),
            "X-Title": os.getenv("OPENROUTER_APP_TITLE", "BernardUdo MCP"),
        },
    )


def _chat_model():
    """OpenRouter (preferred) or OpenAI API via model name string."""
    if os.getenv("OPENROUTER_API_KEY"):
        set_tracing_disabled(True)
        return OpenAIChatCompletionsModel(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            openai_client=_openrouter_client(),
        )
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    raise RuntimeError(
        "Set OPENROUTER_API_KEY for OpenRouter, or OPENAI_API_KEY for OpenAI."
    )


async def run_demo(user_query: str) -> str:
    model = _chat_model()

    params = {
        "command": "uv",
        "args": ["run", str(HERE / "server.py")],
        "cwd": str(HERE),
    }

    async with MCPServerStdio(
        params=params, client_session_timeout_seconds=60
    ) as mcp:
        with trace("bernard_timezone_mcp"):
            agent = Agent(
                name="timezone_helper",
                instructions=INSTRUCTIONS,
                model=model,
                mcp_servers=[mcp],
            )
            result = await Runner.run(
                agent,
                user_query,
            )
            return result.final_output


def main() -> None:
    q = os.getenv(
        "DEMO_QUERY",
        "What is the current local time in Africa/Lagos, and what offset is that from UTC?",
    )
    out = asyncio.run(run_demo(q))
    print(out)


if __name__ == "__main__":
    main()
