from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 2

INSTRUCTIONS = fINSTRUCTIONS = f"""
You are a research planning assistant.

Given a research query, generate {HOW_MANY_SEARCHES} focused academic search queries 
that would help retrieve relevant research papers.

The queries should:
- Be specific and technical
- Reflect how researchers search (not casual Google queries)
- Cover different aspects of the topic (methods, applications, theory, comparisons)

Avoid generic queries. Make them precise and information-rich.
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