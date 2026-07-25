#!/usr/bin/env python3
"""CLI for the home bartender."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=True)

from graph import run_bartender


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    text = " ".join(sys.argv[1:]).strip()
    if not text:
        text = (
            "Got vodka, some bourbon and gin. Tonic water, couple limes, "
            "angostura bitters, simple syrup. No shaker though, just a big "
            "spoon and rocks glasses. Not into super sweet drinks."
        )
    print(run_bartender(text))





if __name__ == "__main__":
    main()
