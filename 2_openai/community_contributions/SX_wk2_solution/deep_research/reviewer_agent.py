from pydantic import BaseModel, Field
from agents import Agent

# Note there is NO writer_agent - reviewer_agent loop to keep it simple
REVIEWER_INSTRUCTIONS = """
You are a professional research report writer.
Review the draft research report given to you.

If acceptable:
APPROVED

Then handoff to the email agent.

If not acceptable:
Rewrite the report then handoff to the email agent.
"""


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


# Hands off to email agent
reviewer_agent = Agent(
    name="Reviewer Agent",
    instructions=REVIEWER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)