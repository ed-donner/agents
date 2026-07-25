"""Run an OpenAI Agents SDK agent wired to the env_align MCP server (Week 6 pattern)."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

HERE = Path(__file__).resolve().parent
FIXTURE_ROOT = HERE / "fixtures" / "sample_project"


async def main() -> None:
    params = {
        "command": "uv",
        "args": ["run", "server.py"],
        "cwd": str(HERE),
    }
    request = (
        f"Using the MCP tools only, audit environment variables for the project at "
        f"{FIXTURE_ROOT}. The local env file is named sample.env (not .env). "
        f"Summarize what is missing or undocumented and suggest next steps."
    )
    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
        agent = Agent(
            name="env_auditor",
            instructions=(
                "You compare .env and .env.example for local projects. "
                "Always call the MCP tools to gather facts; do not invent variable names. "
                "Keep answers short and actionable."
            ),
            model=os.getenv("ENV_ALIGN_MODEL", "gpt-4.1-mini"),
            mcp_servers=[server],
        )
        with trace("env_align_demo"):
            result = await Runner.run(agent, request)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
