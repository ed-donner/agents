"""Planner agent (plan.md Phase C)."""

from __future__ import annotations

import config

from agents import Agent, Runner

from models import SearchPlan


def _instruction() -> str:
    return """You are a research planning agent. Your task is to prepare a number of web search phases helpful to best answer the question.
Make sure to cover all the aspects of the question. Provide reason for each search phrase."""


def _agent() -> Agent:
    return Agent(
        name="PlannerAgent",
        instructions=_instruction(),
        output_type=SearchPlan,
        model=config.MODEL_PLANNER,
    )


async def run_planner(canonical_question: str, phrases_count: int) -> SearchPlan:
    """Planner LLM only; log ``planner: start/end`` in the caller."""
    inp = (
        f"# Question\n{canonical_question}\n\n"
        f"Provide {phrases_count} web search phrases to best answer the question."
    )
    result = await Runner.run(_agent(), inp)
    return result.final_output
