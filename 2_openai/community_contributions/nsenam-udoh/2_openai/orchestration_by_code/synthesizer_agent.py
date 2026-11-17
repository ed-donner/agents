from agents import Agent
from pydantic import BaseModel, Field

from planner_agent import MODEL_NAME, WebSearchItem


class GapReview(BaseModel):
    gaps: list[str]
    follow_up_searches: list[WebSearchItem] = Field(max_length=3)


synthesizer_agent = Agent(
    name="Synthesizer Agent",
    instructions="""
Review the research results against the original query and clarification answers.
Identify material gaps that prevent a complete answer. Propose up to three focused
follow-up searches only when they can fill those gaps. Return no gaps when the
available research is sufficient.
""",
    model=MODEL_NAME,
    output_type=GapReview,
)
