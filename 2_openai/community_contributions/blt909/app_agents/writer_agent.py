from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a catchy newsletter based on a search query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and flow of the report"
    "Then, generate the newsletter and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed, "
    "organized from a journalistic perspective, highlighting the most important findings.\n"
    "Aim for 2-5 pages of content, at least 500 words."
)


class ReportData(BaseModel):
    outline: str = Field(description="An outline for the report that describes the structure and flow of the report")
    markdown_report: str = Field(description="The final newsletter")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


google_api_key = os.getenv('GOOGLE_API_KEY')
model_name = "gemini-3.1-flash-lite-preview"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=ReportData,
)