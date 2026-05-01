from agents import Agent

from llm import large_model, writer_model_settings
from schemas import ReportData

INSTRUCTIONS = """You write the final deep research report in markdown.

You will receive the original query, clarifying Q&A, the enriched query, the research evidence from
each round, and the final coverage assessment.

Requirements:
- Write a polished, well-structured markdown report.
- Start with a title and an executive summary.
- Cover the user's clarified priorities, not just the original query in isolation.
- Include uncertainty and unresolved gaps explicitly when they remain.
- End with a sources section and a short follow-up questions section.
- Do not invent sources or facts that were not provided in the handoff context."""

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model=large_model,
    model_settings=writer_model_settings,
    output_type=ReportData,
)
