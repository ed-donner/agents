from agents import Agent
from pydantic import BaseModel, Field

MODEL_NAME = "gpt-4o-mini"
HOW_MANY_SEARCHES = 3

INSTRUCTIONS = f"""
You are a research assistant. Given a user query and any clarification answers,
come up with web searches that best answer the query. Output at most
{HOW_MANY_SEARCHES} search terms.
"""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


planner_agent = Agent(
    name="Planner Agent",
    instructions=INSTRUCTIONS,
    model=MODEL_NAME,
    output_type=WebSearchPlan,
)
