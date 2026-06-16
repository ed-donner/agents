from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive, well-cited report for a research query. "
    "You will be provided with the original query and research summaries. Each summary may end with a line 'Source: <url or title>'.\n\n"
    "**Citation layer (mandatory):**\n"
    "- In the report body, cite sources using numbered references: [1], [2], [3], etc. Place a citation after any claim that comes from the research.\n"
    "- At the end of the report, add a section: ## Sources and References\n"
    "- Under that section, list numbered entries matching your [1], [2], ... using the 'Source: ...' lines from the research (one number per source; deduplicate if the same source appears).\n"
    "- Format each entry as: [N] <title or URL from the Source line>\n\n"
    "You should first outline the report, then write it. The report should be in markdown, lengthy and detailed (5-10 pages, 1000+ words), with citations throughout and a complete Sources section at the end."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)

writer_agent_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description="Write a long, detailed markdown report from the original query and summarized search results. Pass query and a single string containing all search summaries.",
)