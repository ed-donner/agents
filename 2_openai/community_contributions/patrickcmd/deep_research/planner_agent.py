from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 15 # 5 keep this number low to save costs

def build_planner_instructions(key_focus_areas: list[str] | None = None) -> str:
    base = (
        f"You are a helpful research assistant. Given a query, come up with a set of web searches "
        f"to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."
    )
    if key_focus_areas:
        areas = "\n".join(f"- {area}" for area in key_focus_areas)
        base += (
            f"\n\nThe user has indicated the following key focus areas. "
            f"Ensure your search terms cover these:\n{areas}"
        )
    return base

INSTRUCTIONS = build_planner_instructions()


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini",
    output_type=WebSearchPlan,
)
