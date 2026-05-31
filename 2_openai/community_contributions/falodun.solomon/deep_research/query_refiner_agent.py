from pydantic import BaseModel, Field
from agents import Agent

class RefinedQuery(BaseModel):
    refined_query: str = Field(description="Improved and expanded query", min_length=10, max_length=1000)
    sub_questions: list[str] = Field(description="Optional deeper questions", min_items=0, max_items=3)

INSTRUCTIONS = """
You are an expert researcher.

Given:
- Original query
- Answers to clarifying questions

Produce a refined, detailed research query that:
- Incorporates user intent
- Removes ambiguity
- Expands into a strong research directive
"""

query_refiner_agent = Agent(
    name="QueryRefiner",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=RefinedQuery,
)
