from pydantic import BaseModel, Field
from agents import Agent

from config import model

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description="Exactly 3 clarifying questions to narrow the research scope.")

INSTRUCTIONS = (
    "You are a clarification agent. Given a research query, generate exactly 3 clarifying questions "
    "that narrow the scope. Cover: specific focus, audience or use case, and depth or timeframe. "
    "Open-ended and actionable. Return exactly 3 questions in the specified format."
)

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model=model,
    output_type=ClarifyingQuestions,
)
