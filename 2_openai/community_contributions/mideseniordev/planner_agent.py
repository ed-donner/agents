from agents import Agent
from pydantic import BaseModel, Field

from config import DEFAULT_MODEL

INSTRUCTIONS = """
You are a research planner.

Given a tuned brief, output a focused set of web searches.
- Respect the provided search budget.
- Prioritize credibility and recency.
- Keep queries specific enough to reduce noisy search results.
"""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters for the final report.")
    query: str = Field(description="Search term to execute.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="Ordered list of searches to execute.")


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=WebSearchPlan,
)
