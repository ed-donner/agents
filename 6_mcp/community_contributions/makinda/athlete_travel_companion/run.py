"""CLI entry: Athlete Travel Companion (Week 6 MCP + OpenAI Agents)."""

from __future__ import annotations

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

from pipeline import run_pipeline


async def main() -> None:
    msg = " ".join(sys.argv[1:]).strip()
    if not msg:
        msg = (
            "I'm training through a 4-day work trip to Boulder, CO (from sea level). "
            "Left knee a bit sore after yesterday's flight. "
            "Find a track or public turf I can use and suggest today's session."
        )
    out = await run_pipeline(msg)
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
