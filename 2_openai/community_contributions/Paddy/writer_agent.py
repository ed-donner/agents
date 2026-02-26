from pydantic import BaseModel, Field
from agents import Agent
from config import gemini_model

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, audience and focus context, and initial research.\n"
    "First create an outline, then generate the report in markdown. Use clear headings, bullet points "
    "where appropriate, and a professional tone. Aim for a detailed, well-structured report (at least 800 words)."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report in markdown.")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further.")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=ReportData,
)
