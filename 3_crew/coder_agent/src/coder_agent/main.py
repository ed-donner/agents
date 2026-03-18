#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from coder_agent.crew import CoderAgent

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

import os
from pathlib import Path


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
    # main.py: <repo>/3_crew/coder_agent/src/coder_agent/main.py
    project_root = Path(__file__).resolve().parents[2]  # <repo>/3_crew/coder_agent
    # project_root.parents[1] == <repo>/agents
    repo_root = project_root.parents[1]

    # Load repo root first, then project root (project wins).
    _load_env_file(repo_root / ".env")
    _load_env_file(project_root / ".env")


def run():
    """
    Run the crew.
    """
    _load_env()
    assignment = 'Write a python program to calculate the first 10,000 terms of this series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + ...'
    inputs = {
        'assignment': assignment,
        'current_year': str(datetime.now().year)
    }

    result = CoderAgent().crew().kickoff(inputs=inputs)
    print(result.raw)
   


if __name__ == "__main__":
    run()