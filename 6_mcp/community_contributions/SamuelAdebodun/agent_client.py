"""
OpenAI Agents SDK client: spawns k8s_health MCP over stdio.

Usage (from this folder):
  pip install -r requirements.txt
  set OPENAI_API_KEY=...   # or rely on repo-root .env if loaded elsewhere
  python agent_client.py "Overview + payments namespace health"
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _ROOT.parents[2]  # .../agents

load_dotenv(_REPO_ROOT / ".env", override=False)
load_dotenv(override=False)

DEFAULT_MODEL = os.environ.get("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")

INSTRUCTIONS = """
You are a platform engineer assistant. All Kubernetes data comes from MOCK JSON on the MCP server
— not a live cluster. Say so briefly if the user seems to think this is production.

MCP tools:
- cluster_overview()
- namespace_health(namespace)
- workload_health(namespace, workload)
- incident_summary(namespace)

MCP resource: runbook://k8s/common-issues (remediation patterns).

Answer with: (1) headline status, (2) bullets for problems, (3) concrete next checks.
"""


async def run_k8s_health_agent(user_query: str, timeout_seconds: int = 120) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set (env or .env at repo root).")

    params = {"command": sys.executable, "args": [str(_ROOT / "server.py")]}

    async with MCPServerStdio(
        params=params,
        client_session_timeout_seconds=timeout_seconds,
    ) as mcp:
        with trace("k8s_health_mcp"):
            agent = Agent(
                name="k8s_health",
                instructions=INSTRUCTIONS,
                model=DEFAULT_MODEL,
                mcp_servers=[mcp],
            )
            result = await Runner.run(agent, user_query)
            return str(result.final_output)


async def _main() -> None:
    query = (
        " ".join(sys.argv[1:]).strip()
        or "Call cluster_overview, then namespace_health for payments, then incident_summary for payments."
    )
    out = await run_k8s_health_agent(query)
    print(out)


if __name__ == "__main__":
    asyncio.run(_main())
