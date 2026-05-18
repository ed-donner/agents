#!/usr/bin/env python3
"""CLI entry: policy deep research using OpenAI Agents SDK + web search.

Usage (from repo root, with course venv active):
  python 2_openai/community_contributions/abdussamadbello_policy_deep_research/run.py
  python .../run.py "Your policy question here"

Requires OPENAI_API_KEY in environment (.env at repo root is fine if you load_dotenv elsewhere).
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from research_manager import PolicyResearchManager


async def _main(query: str) -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    manager = PolicyResearchManager()
    report_md: str | None = None
    async for chunk in manager.run(query):
        if chunk.startswith("[status] "):
            print(chunk.removeprefix("[status] "))
        else:
            report_md = chunk

    if report_md:
        print("\n--- Policy brief (markdown) ---\n")
        print(report_md)


def main() -> None:
    load_dotenv(override=True)
    q = " ".join(sys.argv[1:]).strip()
    if not q:
        q = (
            "What are the main US federal themes in recent EPA reporting rules for "
            "greenhouse gas emissions from large facilities?"
        )
    asyncio.run(_main(q))


if __name__ == "__main__":
    main()
