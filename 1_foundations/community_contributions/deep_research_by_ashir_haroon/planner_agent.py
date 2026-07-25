from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are a research planning assistant. You will receive a research query along with 
clarifying Q&A that reveals the user's specific intent, scope, and constraints.

Use the clarifications to craft a highly targeted set of {HOW_MANY_SEARCHES} web searches. Each search 
should be tuned to the user's actual needs rather than being generic. Prioritize searches that address 
the specific angles and constraints the user mentioned in their answers."""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important given the query and clarifications.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches tuned to the clarified query.")


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
