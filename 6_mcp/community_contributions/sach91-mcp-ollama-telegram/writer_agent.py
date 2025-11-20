from pydantic import BaseModel, Field
from agents import Agent
from base_model import ollama_model

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive short report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should generate a concise report and return that as your final output.\n"
    "The final output should be in text format, and it should be concise, not lengthy or detailed. "
    "Aim for 2 paragraphs of content, maximum 300 words."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    text_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=ollama_model,
    output_type=ReportData,
)
