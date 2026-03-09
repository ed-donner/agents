from pydantic import BaseModel, Field
from agents import Agent

ANALYSER_INSTRUCTIONS = """
You are a senior research analyst.
Evaluate the research results given to you.
Return:
- research_complete: True if you think the research looks complete
- research_complete: False if you think the research is not complete
Also provide your reason.
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