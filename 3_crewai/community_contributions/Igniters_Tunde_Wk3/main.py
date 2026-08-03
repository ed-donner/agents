#!/usr/bin/env python
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

from curriculum_planner.crew import CurriculumPlannerCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def _load_env() -> None:
    here = Path.cwd().resolve()
    for base in [here, *here.parents]:
        env_file = base / ".env"
        if env_file.is_file():
            load_dotenv(env_file, override=True)
            return
    load_dotenv(override=True)


def _ensure_gemini_env() -> None:
    """LiteLLM/CrewAI often expect GOOGLE_API_KEY for gemini/*; many users only set GEMINI_API_KEY."""
    gemini = os.getenv("GEMINI_API_KEY", "").strip()
    google = os.getenv("GOOGLE_API_KEY", "").strip()
    if gemini and not google:
        os.environ["GOOGLE_API_KEY"] = gemini


os.makedirs("output", exist_ok=True)

# Edit this before running. Set GEMINI_API_KEY in .env or the environment (GOOGLE_API_KEY also works).
curriculum_brief = """
Build a 3-week introduction to responsible AI for high school STEM club students (1.5-hour weekly sessions).
No coding prerequisite. Cover: what models are, bias and fairness at a high level, privacy basics,
and a final group discussion on acceptable use. Include hands-on activities that do not require paid tools.
"""


def run() -> None:
    _load_env()
    _ensure_gemini_env()

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or a .env file in the project root."
        )

    CurriculumPlannerCrew().crew().kickoff(
        inputs={
            "curriculum_brief": curriculum_brief.strip(),
        }
    )


if __name__ == "__main__":
    run()
