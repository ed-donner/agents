from agents import Agent
from pydantic import BaseModel, Field

from config import DEFAULT_MODEL

INSTRUCTIONS = """
You are a senior research writer.

Input includes the original query, tuned brief, and summarized search findings.
Write a clean markdown report with these sections:
1) Executive Summary
2) Key Findings
3) Analysis
4) Limitations and Open Questions
5) References

Citation rules:
- use numbered inline citations like [1], [2]
- include at least one citation for each non-obvious factual claim
- include matching entries under References
"""


class ReportData(BaseModel):
    short_summary: str = Field(description="2-3 sentence summary.")
    markdown_report: str = Field(description="Full markdown report.")
    follow_up_questions: list[str] = Field(description="Suggested next research questions.")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=ReportData,
    handoff_description="Produce polished cited report from collected findings.",
)
