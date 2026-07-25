from pydantic import (
    BaseModel,
    Field,
)

from agents import Agent


HOW_MANY_SEARCHES = 10

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-5.2",
    output_type=WebSearchPlan,
)

search_planning_tool = planner_agent.as_tool(
    tool_name="web_search_planning_tool",
    tool_description="Generates a plan of web searches to perform given a research query.",
)
