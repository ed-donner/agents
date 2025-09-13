from agents import Agent
from pydantic import BaseModel, Field

class ClarifierOutput(BaseModel):
    questions: list[str] = Field(
        description="Up to 3 clarifying questions for the user."
    )

INSTRUCTIONS = """
You are a Clarifier Agent. Given a query, ask the user up to 3 clarifying questions 
that will help you refine the research. Do not answer the query yet, 
only output the questions as a list.
"""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifierOutput,
)
