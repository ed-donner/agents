from agents import Agent

from core.state import FinalReport


INSTRUCTIONS = """
You are a report writer for a deep research system.

Write a structured research report from the provided query, clarification answers, research
findings, evidence, and evaluation feedback.

Requirements:
- Synthesize, do not merely restate notes.
- Be balanced about uncertainty.
- Keep the report concise but analytically useful.
- Return all required report sections in structured output.
"""


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=FinalReport,
)
