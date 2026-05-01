"""
Week 6 — multi-agent paper auto-trader floor (MCP-backed).

Run from repo root:
  cd agents && uv run python 6_mcp/community_contributions/solarinayo/run_floor.py

Requires OPENAI_API_KEY. Optional POLYGON_API_KEY for US equity hints.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import AsyncExitStack
from pathlib import Path

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

ROOT = Path(__file__).resolve().parent


def _server(script: str) -> dict:
    return {
        "command": "uv",
        "args": ["run", script],
        "cwd": str(ROOT),
    }


SCOUT_INSTRUCTIONS = """You are VenueScout, a multi-exchange routing analyst (paper simulation only).
Use MCP tools only. Steps:
1) Call list_venues to understand venue metadata.
2) For user symbols, call compare_venues and/or get_crypto_quote / get_equity_hint / get_fx_rate as appropriate.
3) Call smart_route with a JSON array string of symbols, matching user risk profile.
Output a concise markdown brief: ranked venues, key risks (liquidity, hours, FX), and data gaps.
Never claim real trades executed. Not financial advice."""


CLERK_INSTRUCTIONS = """You are AutoTraderClerk (paper journal only).
You already have the Scout brief in the user message.
Use MCP tools:
1) get_paper_portfolio to see existing paper state.
2) propose_paper_order for at most 2 hypothetical intents that align with the Scout routing and user goal.
Include routing_context summarizing venue scores from the Scout brief.
If data is missing, record zero orders and explain why.
Not financial advice."""


async def run_floor(
    user_goal: str, symbols: list[str], risk_profile: str = "balanced"
) -> tuple[str, str]:
    intel = _server("exchange_intel_server.py")
    paper = _server("paper_ledger_server.py")
    async with AsyncExitStack() as stack:
        ex = await stack.enter_async_context(MCPServerStdio(intel, client_session_timeout_seconds=120))
        pj = await stack.enter_async_context(MCPServerStdio(paper, client_session_timeout_seconds=120))
        scout = Agent(
            name="VenueScout",
            instructions=SCOUT_INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=[ex],
        )
        sym_json = json.dumps(symbols)
        scout_prompt = (
            f"User goal: {user_goal}\n"
            f"Symbols: {sym_json}\n"
            f"Risk profile: {risk_profile}\n"
            "Produce routing intelligence for paper simulation."
        )
        with trace("solarinayo-scout"):
            scout_result = await Runner.run(scout, scout_prompt, max_turns=25)

        clerk = Agent(
            name="AutoTraderClerk",
            instructions=CLERK_INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=[ex, pj],
        )
        clerk_prompt = (
            f"User goal: {user_goal}\n"
            f"Symbols: {sym_json}\n"
            f"Risk profile: {risk_profile}\n\n"
            f"=== Scout brief ===\n{scout_result.final_output}"
        )
        with trace("solarinayo-clerk"):
            clerk_result = await Runner.run(clerk, clerk_prompt, max_turns=25)

        scout_text = scout_result.final_output or ""
        clerk_text = clerk_result.final_output or ""
        return scout_text, clerk_text


def main() -> None:
    scout, clerk = asyncio.run(
        run_floor(
            user_goal="Smart-route a small diversification check before end of week (paper only).",
            symbols=["BTC", "AAPL"],
            risk_profile="moderate",
        )
    )
    print("\n=== VenueScout ===\n", scout)
    print("\n=== AutoTraderClerk ===\n", clerk)


if __name__ == "__main__":
    main()
