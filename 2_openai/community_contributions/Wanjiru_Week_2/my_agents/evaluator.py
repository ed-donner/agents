from agents import Agent
from pydantic import BaseModel

class Evaluation(BaseModel):
    is_sufficient: bool
    feedback: str

evaluator = Agent(
    name="Evaluator",
    instructions="""
    Evaluate if the research report is complete and detailed.
    If not, explain what is missing.
    """,
    model="gpt-4o-mini",
    output_type=Evaluation,
)
