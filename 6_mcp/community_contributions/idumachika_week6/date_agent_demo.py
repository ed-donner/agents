"""
Week 6 — connect OpenAI Agents SDK to the date MCP server (6_mcp/2_lab2 pattern).

Run from repository root:
  uv run python 6_mcp/community_contributions/idumachika_week6/date_agent_demo.py

Requires OPENAI_API_KEY in agents/.env (OpenRouter sk-or-* supported via env if SDK respects it).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

_AGENTS = Path(__file__).resolve().parents[3]
_SIX_MCP = Path(__file__).resolve().parents[2]

load_dotenv(_AGENTS / ".env")
load_dotenv()

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio


async def main() -> None:
    server_path = Path(__file__).resolve().parent / "date_time_server.py"
    params = {
        "command": "uv",
        "args": ["run", str(server_path)],
        "cwd": str(_SIX_MCP),
    }

    instructions = (
        "You can call MCP tools to get the current date or date-time. "
        "Answer the user using those tools when they ask about today or the time."
    )
    request = (
        "What is today's date in UTC? Also what is the current local time in Africa/Lagos?"
    )
    model = "gpt-4o-mini"

    async with MCPServerStdio(
        params=params, client_session_timeout_seconds=60
    ) as mcp_server:
        agent = Agent(
            name="date_assistant",
            instructions=instructions,
            model=model,
            mcp_servers=[mcp_server],
        )
        with trace("idumachika_week6_date_mcp"):
            result = await Runner.run(agent, request)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
