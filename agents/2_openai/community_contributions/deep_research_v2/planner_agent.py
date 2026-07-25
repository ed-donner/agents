from pydantic import BaseModel
from agents import Agent

DEFAULT_SEARCHES = 5

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches " \
               f"to perform to best answer the query. Output {DEFAULT_SEARCHES} terms to query for."

class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important to the query."

    query: str
    "The search term to use for the web search."

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]
    """A list of web searches to perform to best answer the query."""

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
