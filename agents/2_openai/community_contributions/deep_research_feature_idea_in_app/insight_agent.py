from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are an insight analyzer. Given user feedback, complaints, or trends, identify patterns and summarize a clear product opportunity."
    "Your summary should highlight the user problem and potential business impact."
)

class Insight(BaseModel):
    user_problem: str = Field(description="The core user pain point or opportunity.")
    supporting_evidence: list[str] = Field(description="Key facts, quotes, or data that support the problem.")

insight_agent = Agent(
    name="InsightAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=Insight
)