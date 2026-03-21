"""Research agent + Serper web_search tool (plan.md Phase C)."""

from __future__ import annotations

from datetime import datetime

import config

from agents import Agent, Runner, function_tool

from models import ResearchData, SearchPlan
from serper_client import serper_search


def _todays_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


@function_tool
async def web_search(query: str) -> str:
    """Searches the web for the query and returns a string with results.

    Args:
        query: The query to search for.

    Returns:
        A string with the results of the search.
    """
    return await serper_search(query)


def _instruction() -> str:
    return f"""You are a research agent. Your task is to perform a number of web searches from the list of provided search topics.
You are given a curated list of search topics. For each item in the list, perform a web search for the query and produce a concise summary.

Keep summaries to 3-4 paragraphs and under 500 words. Use guidance from the reason clause for the search to produce succinct and to-the-point summary.
Copy the reason verbatim from input to the output.

# Date
{_todays_date()}
"""


def _agent() -> Agent:
    return Agent(
        name="ResearchAgent",
        instructions=_instruction(),
        output_type=ResearchData,
        tools=[web_search],
        model=config.MODEL_RESEARCH,
    )


async def run_research(plan: SearchPlan) -> ResearchData:
    """Research agent + tools only; log ``research: start/end`` in the caller."""
    inp = f"# Search Topics\n{plan.model_dump_json()}"
    result = await Runner.run(
        _agent(),
        inp,
        max_turns=config.MAX_RESEARCH_TURNS,
    )
    return result.final_output
