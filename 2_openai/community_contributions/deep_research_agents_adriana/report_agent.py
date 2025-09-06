from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')



INSTRUCTIONS = """You are a researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query and some initial research done by a search assistant.
You should first come up with an outline for the report that describes the structure and flow of the report.
Then, generate the report and return that as your final output.
The final output should be in a markdown format, and it should be lengthy and detailed.
Aim for 5-10 pages of content, at least 1000 words.
Come up with 3-5 suggestions of topics that might also be interesting for the user ."""

class ReportData(BaseModel):
    short_summary: str = Field(description = 'A short 2-3 sentences summary of the findings')
    markdown_report: str = Field(description = 'The final report')
    follow_up_questions: list[str] = Field(description = 'Suggested topics to explore further')


report_agent = Agent(
    name = 'ReportAgent',
    instructions = INSTRUCTIONS,
    model = 'gpt-4o-mini',
    output_type = ReportData
)

report_tool = report_agent.as_tool(tool_name = 'final_report', tool_description = 'Write longe, well-structured final report')