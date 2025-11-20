from pydantic import BaseModel, Field
from agents import Agent
from base_model import ollama_model

HOW_MANY_SEARCHES = 2

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a limited set of web searches \
to perform to best answer the query. Output the {HOW_MANY_SEARCHES} terms to query for."


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(
    name="PlannerAgent",
    model=ollama_model,
    instructions=INSTRUCTIONS,
    output_type=WebSearchPlan,
)