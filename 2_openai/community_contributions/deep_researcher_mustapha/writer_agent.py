"""
writer_agent.py — Synthesizes search results into a structured, detailed report.
"""
from agents import Agent
from pydantic import BaseModel, Field
from deep_research import MODEL_CAPABLE


# ── Structured output schema ─────────────────────────────────────────────────

class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report in detailed Markdown format.")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further.")


# ── Agent definition ─────────────────────────────────────────────────────────

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. "
    "Aim for 5-10 pages of content, at least 1000 words. **You MUST include standard Markdown "
    "citations (e.g., [Title](URL)) throughout the report and include a 'Sources' section at the "
    "end with a full list of clickable links.**"
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=MODEL_CAPABLE,
    output_type=ReportData,
)
