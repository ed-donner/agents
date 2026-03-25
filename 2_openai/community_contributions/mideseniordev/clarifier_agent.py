from agents import Agent
from pydantic import BaseModel, Field

from config import DEFAULT_MODEL

INSTRUCTIONS = """
You generate exactly 3 clarifying questions for a research task.

Question 1 must clarify final deliverable and citation format.
Question 2 must clarify allowed tools/search providers and constraints.
Question 3 must clarify evaluation/demo expectations.

Keep each question concise and concrete.
"""


class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly 3 clarifying questions ordered by importance.",
        min_length=3,
        max_length=3,
    )


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=ClarificationQuestions,
)
