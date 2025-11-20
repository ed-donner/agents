from pydantic import BaseModel, Field
from agents import Agent
from base_model import ollama_model
from writer_agent import ReportData

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive short report for a research query. "
    "You will be provided with the original query.\n"
    "You should generate a concise report and return that as your final output.\n"
    "The final output should be in text format, and it should be concise, not lengthy or detailed. "
    "Aim for 2 paragraphs of content, maximum 200 words."
)

main_agent = Agent(
    name="MainAgent",
    instructions=INSTRUCTIONS,
    model=ollama_model,
    output_type=ReportData,
)
