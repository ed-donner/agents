from pydantic import BaseModel
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words.\n\n"
    
    "IMPORTANT SOURCE HANDLING:\n"
    "- Preserve all source URLs and references from the research summaries\n"
    "- Include inline citations throughout your report using the format: [Source Name](URL)\n"
    "- At the end of your report, create a dedicated '## Sources and References' section\n"
    "- In the Sources section, list all unique URLs mentioned in the report in a numbered list\n"
    "- Format sources as: '1. [Website Name/Title](full URL)'\n"
    "- Ensure no source links are lost during synthesis\n"
    "- If you cannot find source URLs in the research, note 'Sources: Based on web research summaries'"
)


class ReportData(BaseModel):
    short_summary: str
    """A short 2-3 sentence summary of the findings."""

    markdown_report: str
    """The final report"""

    follow_up_questions: list[str]
    """Suggested topics to research further"""


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)