from agents import Agent
from pydantic import BaseModel, Field

from planner_agent import MODEL_NAME


class EvaluationScore(BaseModel):
    score: int = Field(ge=1, le=10)
    reason: str


evaluator_agent = Agent(
    name="Evaluator Agent",
    instructions="""
Evaluate only the supplied report for accuracy, completeness, coherence, and
usefulness. Score it from 1 to 10 and briefly explain the score. Do not suggest
or perform another research round.
""",
    model=MODEL_NAME,
    output_type=EvaluationScore,
)
