from pydantic import BaseModel, Field
from agents import Agent
from datetime import datetime

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"You are a research assistant for a company. \
Given the company name, industry and a research query, come up with a set of web searches to perform to best answer the query considering areas such as \
user or customer feedback, competitor analytics, market trends, etc. The current date is {datetime.now().strftime('%Y-%m-%d')}. \
Output {HOW_MANY_SEARCHES} terms to query for.  Ensure the search queries are specific to the company."

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan
)