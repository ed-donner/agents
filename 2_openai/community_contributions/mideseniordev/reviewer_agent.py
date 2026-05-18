from agents import Agent
from pydantic import BaseModel, Field

from config import DEFAULT_MODEL

INSTRUCTIONS = """
You are a research quality reviewer.

Improve the provided markdown report for clarity, internal consistency, and citation hygiene.
Do not invent facts. Keep original meaning intact.
Return the improved markdown only.
"""


class ReviewedReport(BaseModel):
    markdown_report: str = Field(description="Final reviewed markdown report.")


reviewer_agent = Agent(
    name="ReviewerAgent",
    instructions=INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=ReviewedReport,
    handoff_description="Review and polish report quality before final delivery.",
)
