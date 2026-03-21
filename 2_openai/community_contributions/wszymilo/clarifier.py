"""Clarifier agent (plan.md Phase C)."""

from __future__ import annotations

import config

from agents import Agent, Runner

from models import ClarificationQuestions


def _instruction() -> str:
    return "You are Clarification Agent tasked to prepare follow-up questions to resolve query ambiguity."


def _agent() -> Agent:
    return Agent(
        name="Clarifier Agent",
        instructions=_instruction(),
        output_type=ClarificationQuestions,
        model=config.MODEL_CLARIFIER,
    )


async def run_clarifier(canonical_question: str, aspects: list[str]) -> list[str]:
    """LLM clarifier only; log ``clarifier: start/end`` in the caller."""
    payload = (
        f"# Original Query\n{canonical_question}\n\n"
        f"# Ambiguous Aspects Found\n{aspects}\n\n"
        "Provide follow-up questions to resolve the ambiguity in the query."
    )
    result = await Runner.run(_agent(), payload)
    return list(result.final_output.questions)
