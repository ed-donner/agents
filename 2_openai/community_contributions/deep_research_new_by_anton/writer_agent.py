from agents import Agent
from ai_model import anthropic_model
from response_model import ReportData

INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query, and some research.
Generate a comprehensive report based on the research and the query.
The final output should be in markdown format, and it should be lengthy and detailed. Aim
for 5-10 pages of content, at least 1000 words.
"""
writer_agent = Agent(
    name="Writer Agent",
    instructions=INSTRUCTIONS,
    model=anthropic_model,
    output_type=ReportData,
)
