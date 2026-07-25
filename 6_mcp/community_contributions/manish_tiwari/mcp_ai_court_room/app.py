#!/usr/bin/env python3
"""
AI Courtroom Debate Simulator — entrypoint.

Run from this directory:
  python app.py

Loads environment from `.env` (here or repo root), starts Gradio UI.
MCP stdio server is spawned automatically when you begin a trial (see debate engine).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=False)
# Repo-level secrets (optional)
_repo_env = ROOT.parent.parent.parent.parent / ".env"
if _repo_env.is_file():
    load_dotenv(_repo_env, override=False)

from ui.gradio_ui import launch_ui


def main() -> None:
    launch_ui()


if __name__ == "__main__":
    main()
