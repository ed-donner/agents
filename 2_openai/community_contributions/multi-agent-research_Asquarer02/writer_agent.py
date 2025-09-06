from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with:\n"
    "1. The original query\n"
    "2. The clarifying questions and their answers\n"
    "3. The search results from multiple sources\n\n"
    "Your process should be:\n"
    "1. First create a detailed outline that reflects the structure and flow of the report\n"
    "2. Then generate a comprehensive report that synthesizes all the information\n"
    "3. Ensure the report directly addresses the original query and incorporates insights from the clarifications\n"
    "4. Include relevant citations and references\n\n"
    "The final output should be in markdown format, detailed and well-structured. "
    "Aim for 5-10 pages of content (at least 1000 words)."
)

class ReportData(BaseModel):
    short_summary: str = Field(description="A concise 2-3 sentence summary of the key findings")
    markdown_report: str = Field(description="The complete research report in markdown format")
    key_insights: list[str] = Field(description="List of the most important insights from the research")
    follow_up_questions: list[str] = Field(description="Suggested topics for further research")
    sources: list[str] = Field(description="List of sources referenced in the report")

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
) 