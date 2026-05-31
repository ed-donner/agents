from pydantic import BaseModel, Field
from agents import Agent
HOW_MANY_SEARCHES = 5

#I refine the wordings of the instructions to be more specific and to the point.
INSTRUCTIONS = f"""
You are a helpful research assistant.

Given a query, generate {HOW_MANY_SEARCHES} useful and relevant search queries.

Try to:
- cover different angles
- avoid repeating the same idea
- keep queries clear and practical
"""

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="openai/gpt-4o-mini",
    output_type=WebSearchPlan,
)