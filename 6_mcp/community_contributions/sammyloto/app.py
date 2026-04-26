"""
Interactive agronomy assistant: OpenAI Agents + local agronomy MCP (stdio).

Requires OPENAI_API_KEY. Run from this directory: python app.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

_ROOT = Path(__file__).resolve().parent

load_dotenv(override=True)


async def main() -> None:
    params = {
        "command": sys.executable,
        "args": [str(_ROOT / "mcp_server.py")],
        "cwd": str(_ROOT),
    }
    mcp = MCPServerStdio(params, client_session_timeout_seconds=60)
    await mcp.connect()

    instructions = """
You are a concise agronomy planning assistant. You have MCP tools for illustrative crop planning:
GDD sums, planting-window hints, soil water snapshots, rotation scores, pest risk bands,
nutrient placeholders, and integrated field briefs.

Rules:
1. Use tools whenever the user asks for numbers, comparisons, or zone/crop-specific guidance.
2. Always state clearly that tool outputs are synthetic demos—not prescriptions for real farms.
3. If a user omits zone, crop, or dates, ask briefly or suggest sensible defaults from list_agro_zones / list_crop_codes.
4. Keep answers practical: bullet summaries after tool calls when helpful.
"""

    agent = Agent(
        name="Agronomy Advisor",
        instructions=instructions,
        mcp_servers=[mcp],
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

    print("Agronomy Advisor — type 'exit' to quit.")
    print("Ask about crops, zones (HRV-HIGH, SAV-MID, MED-COAST), GDD, rotation, or water.\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"exit", "quit", "bye"}:
                print("Good luck with the season.")
                break
            if not user_input:
                continue
            with trace("Agronomy Advisor"):
                result = await Runner.run(agent, user_input, max_turns=15)
            print(f"\nAdvisor:\n{result.final_output}")
        except KeyboardInterrupt:
            print("\nGood luck with the season.")
            break


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY (e.g. in .env).")
        sys.exit(1)
    asyncio.run(main())
