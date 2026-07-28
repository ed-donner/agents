"""
Week 6 demo: OpenAI Agents SDK + Kirundi Brain MCP (stdio).

Usage (from this directory):
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env   # add OPENAI_API_KEY
  python demo_agent.py "Teach me Kirundi greetings"
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

_CONTRIB = Path(__file__).resolve().parent
load_dotenv(_CONTRIB / ".env", override=True)

INSTRUCTIONS = """
You are a Kirundi (Rundi) study coach for learners interested in Burundi.
You ONLY know what your MCP tools return from the Kirundi Brain.

Rules:
- Call tools before teaching vocabulary; do not invent phrases.
- Prefer brain_search_notes / brain_read_file / ask_kirundi_tutor.
- Check profile_get once per session; update profile after clear mistakes.
- Keep replies short: phrase, meaning, one example, optional tip.
- For destructive writes/deletes, ask the human first, then pass the confirm flags.
"""


async def run_demo(user_query: str) -> str:
    """Run one agent turn with the Kirundi Brain MCP server attached."""
    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        raise RuntimeError("Set OPENAI_API_KEY in .env before running the demo agent.")

    env = {
        **os.environ,
        "KIRUNDI_BRAIN_DIR": str(_CONTRIB / "brain"),
        "KIRUNDI_BRAIN_DATA_DIR": str(_CONTRIB / "data"),
    }
    params = {
        "command": sys.executable,
        "args": [str(_CONTRIB / "server.py")],
        "cwd": str(_CONTRIB),
        "env": env,
    }

    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
        agent = Agent(
            name="KirundiCoach",
            instructions=INSTRUCTIONS,
            model=os.getenv("KIRUNDI_BRAIN_MODEL", "gpt-4o-mini"),
            mcp_servers=[server],
        )
        with trace("kirundi_brain_demo"):
            result = await Runner.run(agent, user_query)
        return str(result.final_output)


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or "Teach me basic Kirundi greetings for a visitor."
    print(asyncio.run(run_demo(query)))


if __name__ == "__main__":
    main()
