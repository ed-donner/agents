from pydantic import BaseModel, Field
from agents import Agent

from config import model

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = (
    f"You are a helpful research assistant. You are given the original query and the user's answers "
    f"to clarifying questions. Come up with {HOW_MANY_SEARCHES} web search terms to best answer the "
    "refined query. Take the clarifications into account. Output the list in the schema provided."
)

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=model,
    output_type=WebSearchPlan,
)

planner_agent_tool = planner_agent.as_tool(
    tool_name="search_planner_tool",
    tool_description="Plans web searches; pass the query and the user's clarification answers.",
)
