from typing import List

from dotenv import load_dotenv
from agents import Agent, ModelSettings
from pydantic import BaseModel, Field
from guardRails import guard_report_emojis
from email_agent import send_email

load_dotenv(override=True)

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words." \
    "CRITICAL FORMATTING RULE : Do not include ANY emojis, icons, or pictorial symbols anywhere " \
    "You are also provided with a handoff for sending out the final reports as an email."
)

class ReportData(BaseModel):
    summary : str = Field(description='A 2-3 line summary of the report')
    markdownReport : str = Field(description=' The final report')
    followUpQuestions : list[str] = Field(description='Suggested follow up questions for the user')

writer_agent = Agent(name='writer_agent',
                     instructions=INSTRUCTIONS,
                     model='gpt-4o-mini',
                     output_type=ReportData,
                     output_guardrails=[guard_report_emojis],
                     model_settings=ModelSettings(max_tokens=4000))