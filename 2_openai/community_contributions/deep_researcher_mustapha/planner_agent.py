"""
planner_agent.py — Decides which web searches to run for a given query.
"""
from agents import Agent
from pydantic import BaseModel, Field
from deep_research import LITELLM_FAST

HOW_MANY_SEARCHES = 3

# ── Structured output schema ─────────────────────────────────────────────────

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


# ── Agent definition ─────────────────────────────────────────────────────────

INSTRUCTIONS = (
    f"You are a helpful research assistant. Given a query, come up with a set of web searches "
    f"to perform to best answer the query. Output {HOW_MANY_SEARCHES} search terms."
)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=LITELLM_FAST,
    output_type=WebSearchPlan,
)
