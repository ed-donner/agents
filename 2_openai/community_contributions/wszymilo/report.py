"""Report agent (plan.md Phase C)."""

from __future__ import annotations

import config

from agents import Agent, Runner

from models import Report, ResearchData


def _instruction() -> str:
    return """You are Senior Researcher writing a comprehensive report. Your task is to generate markdown-formatted report based on the research materials.
You will be given:
 * Original question
 * Research materials containing results of prior searches

Your task is to synthesize the research materials into a comprehensive report that addresses the original question. Aim for 1000+ words long report.
Make sure that the report is:
 * Comprehensive and well-structured
 * Clearly written and easy to follow
 * If it references any measurable values, keep the units the same (convert if needed)
"""


def _agent() -> Agent:
    return Agent(
        name="Report Agent",
        instructions=_instruction(),
        output_type=Report,
        model=config.MODEL_REPORT,
    )


async def run_report(canonical_question: str, research: ResearchData) -> Report:
    """Report LLM only; log ``report: start/end`` in the caller."""
    inp = (
        f"# Original Question\n{canonical_question}\n\n"
        f"# Research Materials\n{research.model_dump_json()}"
    )
    result = await Runner.run(_agent(), inp)
    return result.final_output
