from agents import Agent
from pydantic import BaseModel

class SearchItem(BaseModel):
    query: str
    reason: str

class SearchPlan(BaseModel):
    searches: list[SearchItem]

planner = Agent(
    name="Planner",
    instructions="""
    Generate 5 useful search queries for the given research topic.
    """,
    model="gpt-4o-mini",
    output_type=SearchPlan,
)
