from pydantic import BaseModel, Field
from agents import Agent

from config import model

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, the user's clarification answers, and research from a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words. Use the clarifications to focus the report."
)

class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=model,
    output_type=ReportData,
)

writer_agent_tool = writer_agent.as_tool(
    tool_name="writing_tool",
    tool_description="Writes the research report from the query, clarification answers, and search summaries.",
)
