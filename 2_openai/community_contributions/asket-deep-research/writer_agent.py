from pydantic import BaseModel, Field
from agents import Agent

from config import WRITER_MODEL_SETTINGS
from guardrails import guardrail_report_quality, guardrail_report_safety


INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You are provided with the original query, and initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(
        description="Suggested topics to research further"
    )


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
    model_settings=WRITER_MODEL_SETTINGS,
    output_guardrails=[guardrail_report_quality, guardrail_report_safety],
)
