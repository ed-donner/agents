#!/usr/bin/env python
"""Run lesson-plan crew: research → author → critic. Uses GEMINI_API_KEY → GOOGLE_API_KEY."""
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from igniters_week3.crew import LessonPlanCrew

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
    gemini = os.getenv("GEMINI_API_KEY", "").strip()
    google = os.getenv("GOOGLE_API_KEY", "").strip()
    if gemini and not google:
        os.environ["GOOGLE_API_KEY"] = gemini


def run():
    _load_env()
    _ensure_gemini_env()

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env — see README.md"
        )

    inputs = {
        "topic": "Introduction to agentic AI patterns (tools, planning, multi-agent handoffs)",
        "audience": "Final-year CS students and junior developers in Africa",
        "level": "Intermediate (comfortable with Python and basic APIs)",
        "duration_minutes": "90",
    }

    try:
        result = LessonPlanCrew().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise RuntimeError(f"An error occurred while running the crew: {e}") from e


def train():
    inputs = {
        "topic": "Using Git branches for team workflows",
        "audience": "Bootcamp students",
        "level": "Beginner",
        "duration_minutes": "60",
    }
    try:
        LessonPlanCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise RuntimeError(f"An error occurred while training the crew: {e}") from e


def replay():
    try:
        LessonPlanCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise RuntimeError(f"An error occurred while replaying the crew: {e}") from e


def test():
    inputs = {
        "topic": "Test-driven development in Python",
        "audience": "Professional developers",
        "level": "Intermediate",
        "duration_minutes": "75",
        "current_year": str(datetime.now().year),
    }
    try:
        LessonPlanCrew().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise RuntimeError(f"An error occurred while testing the crew: {e}") from e
