from agents import Agent
from pydantic import BaseModel, Field

from planner_agent import MODEL_NAME


class ClarifyingQuestion(BaseModel):
    question: str
    reason: str


class ClarifyingQuestions(BaseModel):
    questions: list[ClarifyingQuestion] = Field(min_length=2, max_length=4)


clarifier_agent = Agent(
    name="Clarifier Agent",
    instructions="""
You help scope research requests. Ask between two and four concise clarifying
questions that would materially improve the research. Explain why each answer
will help. Do not ask for information already present in the query.
""",
    model=MODEL_NAME,
    output_type=ClarifyingQuestions,
)
