"""Evaluator agent: pass/fail report quality + gaps + suggested searches (plan.md Phase I)."""

from __future__ import annotations

import config

from agents import Agent, Runner

from models import EvaluationResult, Report, ResearchData


def _instruction() -> str:
    return """You are a strict research quality evaluator.

Given the user's original question, the research material gathered, and the draft markdown report:
- Decide whether the report **fully and accurately** answers the question using the evidence available.
- If it passes, set passes=true and use empty lists for gaps and suggested_searches.
- If it fails, set passes=false, list concrete **gaps** (missing coverage, weak sourcing, factual issues), and suggest **short web search queries** (suggested_searches) that would help fix the report.

Be concise: gaps are short bullet-style strings; suggested_searches are query strings only."""


def _agent() -> Agent:
    return Agent(
        name="Evaluator Agent",
        instructions=_instruction(),
        output_type=EvaluationResult,
        model=config.MODEL_EVALUATOR,
    )


async def run_evaluator(
    canonical_question: str,
    report: Report,
    research: ResearchData,
) -> EvaluationResult:
    """LLM evaluation only; log ``evaluator: start/end`` in the caller."""
    inp = (
        f"# Original Question\n{canonical_question}\n\n"
        f"# Research Materials\n{research.model_dump_json()}\n\n"
        f"# Draft Report (markdown)\n{report.markdown_report}\n\n"
        f"# Summary\n{report.summary}\n"
    )
    result = await Runner.run(_agent(), inp)
    return result.final_output
