#!/usr/bin/env python
import os
import sys
import warnings
from pathlib import Path

from datetime import datetime

from finance_research.crew import FinanceResearch

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'").strip('"')
        # Set if missing OR present-but-empty
        if k and (k not in os.environ or not os.environ.get(k)):
            os.environ[k] = v

def _load_env() -> None:
    """
    Load API keys from repo-level and project-level `.env` files (if present).
    This makes `crewai run` pick up OPENAI_API_KEY without manual exporting.
    """
    # File is: <repo_root>/3_crew/finance_research/src/finance_research/main.py
    project_root = Path(__file__).resolve().parents[2]  # <repo_root>/3_crew/finance_research
    repo_root = project_root.parents[1]  # <repo_root>

    # Prefer python-dotenv when available, otherwise fall back to a minimal parser.
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]

        load_dotenv(repo_root / ".env", override=False)     # <repo_root>/.env
        load_dotenv(project_root / ".env", override=False)  # project-local .env (optional)
    except Exception:
        _load_env_file(repo_root / ".env")
        _load_env_file(project_root / ".env")

def run():
    """
    Run the crew.
    """
    _load_env()
    now = datetime.now()
    inputs = {
        'company': 'Tesla',
        'current_year': str(now.year),
        'current_date': now.date().isoformat(),
    }
    result = FinanceResearch().crew().kickoff(inputs=inputs)
    print(result.raw)

if __name__ == "__main__":
    run()