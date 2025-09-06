# clarifier_agent.py

from pydantic import BaseModel, Field
from typing import List
from agents import Agent

INSTRUCTIONS = """
You are a helpful research assistant. Your goal is to clarify the user's query to ensure the research meets their needs.
If the query is vague, ambiguous, or broad, ask up to 3 short, specific clarifying questions.
If the query is already very clear, return an empty list.

Only include questions that will help improve search results or report relevance.
"""

class ClarificationQuestions(BaseModel):
    questions: List[str] = Field(description="A list of up to 3 clarifying questions.")

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
)
