from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher writing a cohesive markdown report. You receive the original brief, "
    "user clarifications, and summarized web findings. Outline mentally, then produce a detailed report "
    "(aim for at least 1000 words when the material supports it). Be structured with headings and bullets "
    "where helpful."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="2–3 sentence executive summary.")
    markdown_report: str = Field(description="Full markdown report.")
    follow_up_questions: list[str] = Field(
        description="Suggested directions for further research."
    )


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)
