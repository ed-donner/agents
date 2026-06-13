import os
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel

INSTRUCTIONS = (
    "You are a senior analyst in a startup due diligence pipeline. "
    "You will be provided with the original startup idea and raw research findings from a research agent.\n"
    "First, outline the structure of the report. Then write the full report based on that outline.\n"
    "The report must be in markdown format, detailed and well-structured. "
    "Cover market opportunity, competitive landscape, product viability, key risks, and investment recommendation. "
    "Aim for 1000-1500 words minimum."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A 2-3 sentence executive summary of the due diligence findings.")

    markdown_report: str = Field(description="The full due diligence report in markdown.")

    follow_up_questions: list[str] = Field(description="Key questions an investor should investigate further.")


gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash-lite",
    openai_client=AsyncOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ.get("GEMINI_API_KEY"),
    ),
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=ReportData,
)