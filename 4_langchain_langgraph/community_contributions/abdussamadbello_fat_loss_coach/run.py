#!/usr/bin/env python3
"""CLI entry for the fat-loss coach graph."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=True)

from coach_graph import run_coach


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY.", file=sys.stderr)
        sys.exit(1)
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        text = (
            "Goal: lose 15 lb in 3 months. Remote work, 35 min/day, $70/week food, "
            "no gym membership (bodyweight + bands $40), vegetarian, mild asthma."
        )
    print(run_coach(text))


if __name__ == "__main__":
    main()
