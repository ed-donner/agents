# planner_agent.py

from pydantic import BaseModel
from agents import Agent

HOW_MANY_SEARCHES = 20

INSTRUCTIONS = """
You are a helpful research assistant. You will be given:
  • Original query  
  • A list of clarifying questions AND their answers  
Using that, come up with a set of 20 focused web-search queries 
that best answer the refined question.  
Return a WebSearchPlan as before.
"""

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
