from pydantic import BaseModel, Field
from agents import Agent

reporter_agent_instructions = (
    "You are a senior cybersecurity analyst tasked with writing a cohesive report for a URL security check. "
    "You will be provided with the original URL and the results of multiple security checks performed by security agents.\n"
    "First, create an outline summarizing the key risks, potential threats, and safe/unsafe aspects. "
    "Then, generate a detailed final report in markdown format.\n"
    "The report should be thorough, clear, and actionable, suitable for a non-technical user to understand.\n"
    "Include recommendations for next steps or verification, if relevant."
)

class UrlReportData(BaseModel):
    url: str = Field(description="Url that was a subject of analysis")
    short_summary: str = Field(description="A short 2-3 sentence summary of the URL's safety and risks.")
    markdown_report: str = Field(description="The detailed final report in markdown format. Embed safly analyzed url on top of report")
    follow_up_checks: list[str] = Field(description="Suggested additional security checks or monitoring steps.")

reporter_agent = Agent(
    name="UrlReporterAgent",
    instructions=reporter_agent_instructions,
    model="gpt-4o-mini",
    output_type=UrlReportData,
)