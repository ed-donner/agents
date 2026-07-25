from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from core.orchestrator import DeepResearchRuntime


def _load_env() -> None:
    load_dotenv(override=True)

    repo_root = Path(__file__).resolve().parents[3]
    fallback_env = repo_root / ".env"
    if fallback_env.exists():
        load_dotenv(fallback_env, override=False)


def prompt_for_answers(questions: list[str]) -> list[str]:
    print("\nBefore starting research I have a few clarifying questions:\n")
    answers: list[str] = []
    for index, question in enumerate(questions, start=1):
        answer = input(f"{index}. {question}\n> ").strip()
        answers.append(answer or "No additional preference provided.")
    return answers


def print_event(message: str) -> None:
    print(f"[runtime] {message}")


async def main() -> None:
    _load_env()

    query = os.environ.get("DEEP_RESEARCH_QUERY") or input("What topic would you like to research?\n> ").strip()
    runtime = DeepResearchRuntime()
    state = await runtime.run(query=query, answer_provider=prompt_for_answers, event_handler=print_event)

    if state.final_report is None:
        print("\nNo final report was generated.")
        return

    print()
    print(state.final_report.as_markdown())


if __name__ == "__main__":
    asyncio.run(main())
