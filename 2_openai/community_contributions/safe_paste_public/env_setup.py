"""Load `.env` from this folder or any parent (e.g. repo root)."""

from pathlib import Path

from dotenv import load_dotenv


def load_repo_env() -> None:
    here = Path(__file__).resolve().parent
    for d in [here, *here.parents[:12]]:
        candidate = d / ".env"
        if candidate.is_file():
            load_dotenv(candidate, override=True)
            return
    load_dotenv(override=True)
