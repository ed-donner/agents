#!/usr/bin/env python
"""Run the CrewAI framework helper crew."""

from __future__ import annotations

import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

from crewai_framework_helper.crew import FrameworkHelperCrew
from rag.paths import project_root

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

DEFAULT_QUESTION = "How do I use CrewBase with YAML agent configs?"
SOURCES_NOTE_MARKER = "**Note:** Source paths above"
GITHUB_UPSTREAM = "https://github.com/crewAIInc/crewAI"


def answer_path() -> Path:
    return project_root() / "output" / "answer.md"


def sources_note() -> str:
    upstream = os.getenv("UPSTREAM_DIR", "upstream/crewai")
    return (
        f"\n> {SOURCES_NOTE_MARKER} are relative to `{upstream}/` on the machine "
        "where this answer was generated. If you have not run "
        "`uv run bootstrap-index --yes`, or your upstream ref differs, the same "
        f"files may be missing locally. See [crewAIInc/crewAI on GitHub]({GITHUB_UPSTREAM}) "
        "for canonical docs.\n"
    )


def append_sources_note(path: Path | None = None) -> None:
    path = path or answer_path()
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if SOURCES_NOTE_MARKER in text:
        return
    path.write_text(text.rstrip() + sources_note(), encoding="utf-8")


def run() -> None:
    load_dotenv()
    question = os.getenv("QUESTION", DEFAULT_QUESTION)
    inputs = {"question": question}
    FrameworkHelperCrew().crew().kickoff(inputs=inputs)
    append_sources_note()


if __name__ == "__main__":
    run()
