"""Triage agent (plan.md Phase C)."""

from __future__ import annotations

import config

from agents import Agent, Runner

from models import TriageResults


def _instruction() -> str:
    return """You are query Triager tasked with inspecting the query for ambiguity.

If the query is clear and unambiguous, return TriageResults with is_ambiguous set to False.
If the query is ambiguous, return TriageResults with is_ambiguous set to True and a list of things that are ambiguous in the query.
"""


def _agent() -> Agent:
    return Agent(
        name="Triage Agent",
        instructions=_instruction(),
        output_type=TriageResults,
        model=config.MODEL_TRIAGE,
    )


async def run_triage(canonical_question: str) -> TriageResults:
    """LLM triage only; log ``triage: start/end`` in the caller (for Gradio streaming)."""
    result = await Runner.run(_agent(), f"# Query\n{canonical_question}")
    return result.final_output
