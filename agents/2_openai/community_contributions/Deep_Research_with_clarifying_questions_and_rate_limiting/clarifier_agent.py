from pydantic import BaseModel
from agents import Agent

class ClarifyingQuestions(BaseModel):
    questions: list[str]
    """Three clarifying questions to better understand the user's query."""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=(
        "You are a research assistant. Your task is to ask 3 clarifying questions that help refine and understand "
        "a research query better. After the user answers them, hand off control to the Research Coordinator to perform the full research."
    ),
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)
