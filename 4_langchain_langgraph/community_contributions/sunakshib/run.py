#!/usr/bin/env python3
"""CLI entry for the lifestyle coach graph."""

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
            "My budget is 50/week, I live in Seattle, 7 hours in school. "
            "5'8\", 150lbs, Male. Studying Math, Science, History. "
            "Grades: Math B, Science A, History C."
        )
    print(run_coach(text))

if __name__ == "__main__":
    main()
