from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a research query specialist. Given an original research query and the user's
answers to clarifying questions, produce a single refined query that will drive targeted web searches.

Your refined query must:
1. Incorporate the specific details, constraints, and angles from the user's answers
2. Be precise and well-scoped — not a vague restatement of the original
3. Reflect the exact intent: audience, time range, geography, depth, or use case specified

Also extract the key constraints as a short list (e.g. "UK market", "2024–2025", "enterprise audience").
These will be used to further focus the search agent.
"""


class RefinedQuery(BaseModel):
    refined_query: str = Field(
        description=(
            "A precise, enriched version of the original query that incorporates all clarifications. "
            "This will be used directly as the research question for web searches."
        )
    )
    search_constraints: list[str] = Field(
        description=(
            "Key constraints or focus areas derived from the clarifications "
            "(e.g. 'UK market only', '2024–2025 data', 'enterprise audience'). "
            "Empty list if none apply."
        )
    )


refiner_agent = Agent(
    name="QueryRefinerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=RefinedQuery,
)
