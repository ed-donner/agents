from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os

load_dotenv(override=True)

BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "openai/gpt-4o-mini")

openrouter_client = AsyncOpenAI(base_url=BASE_URL, api_key=OPENROUTER_API_KEY)
model = OpenAIChatCompletionsModel(openai_client=openrouter_client, model=MODEL_NAME)


INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query, and some research.
Generate a comprehensive report based on the research and the query.
The final output should be in markdown format, and it should be lengthy and detailed. Aim 
for 5-10 pages of content, at least 1000 words.
"""


class ReportData(BaseModel):
    short_summary: str = Field(
        description="A short 2-3 sentence summary of the findings."
    )
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(
        description="Suggested topics to research further"
    )


writer_agent = Agent(
    name="Writer Agent",
    instructions=INSTRUCTIONS,
    model=model,
    output_type=ReportData,
)
