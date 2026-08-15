from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

gemini_model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=gemini_client
)

INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query, and some research.
Generate a comprehensive report based on the research and the query.
The final output should be in markdown format, and it should be lengthy and detailed. Aim 
for 5-10 pages of content, at least 1000 words.
"""


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(name="Writer Agent", instructions=INSTRUCTIONS, model=gemini_model, output_type=ReportData)
