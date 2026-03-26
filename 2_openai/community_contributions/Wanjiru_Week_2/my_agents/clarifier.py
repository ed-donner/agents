from agents import Agent
from pydantic import BaseModel

class ClarificationOutput(BaseModel):
    questions: list[str]

clarifier = Agent(
    name="Clarifier",
    instructions="""
    Given a research query, generate 2-3 clarifying questions if needed.
    Keep them short and useful.
    """,
    model="gpt-4o-mini",
    output_type=ClarificationOutput,
)
