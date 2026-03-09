from pydantic import BaseModel, Field
from agents import Agent

ANALYSER_INSTRUCTIONS = """
You are a senior research analyst.
Evaluate the research results given to you.

Return:
- research_complete: True if you think the research looks broadly complete.
- research_complete: False if you think the research is significantly incomplete.
- reason: Briefly explain why you think the research is complete or what crucial information is missing.
"""


class EvaluateOutput(BaseModel):
    research_complete: bool = Field(description="Is the research complete?")
    reason: str = Field(description="Explain what information could be missing.")


analyser_agent = Agent(
    name="Analyser Agent",
    instructions=ANALYSER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluateOutput,
)