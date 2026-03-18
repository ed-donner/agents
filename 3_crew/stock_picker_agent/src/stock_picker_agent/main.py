#!/usr/bin/env python
import os
import sys
import warnings
from pathlib import Path

from datetime import datetime

from stock_picker_agent.crew import StockPickerAgent

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def _load_env_file(path: Path) -> None:
    """
    Minimal .env loader (no dependency on python-dotenv).
    Sets variables if missing or empty.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'").strip('"')
        if k and (k not in os.environ or not os.environ.get(k)):
            os.environ[k] = v


def _load_env() -> None:
    # main.py: <repo>/3_crew/stock_picker_agent/src/stock_picker_agent/main.py
    project_root = Path(__file__).resolve().parents[2]  # <repo>/3_crew/stock_picker_agent
    # project_root.parents[1] == <repo>/agents
    repo_root = project_root.parents[1]

    # Load repo root first, then project root (project wins).
    _load_env_file(repo_root / ".env")
    _load_env_file(project_root / ".env")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    _load_env()
    inputs = {
        'sector': 'Financial Services',
        # Some agent templates reference {company}; this crew mostly operates on
        # a discovered list of companies, so we provide a safe default.
        'company': 'NSE:ICICIBANK',
    }

    result = StockPickerAgent().crew().kickoff(inputs=inputs)
    print("\n\n=== FINAL DECISION ===\n\n")
    print(result.raw)

if __name__ == "__main__":
    run()
