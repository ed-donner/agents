from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = f"""
You are a senior editor and a harsh critic. You will be given an original research query and a final draft of a 1000-word report.
Your job is to check if the report *fully* answers the query, is well-structured, accurate, and meets the length requirement.
If it's not perfect, set is_approved to false and provide clear revisions.
"""

class ReportEvaluation(BaseModel):
    is_approved: bool = Field(description="Is this report high-quality, accurate, well-structured, and ready to be sent to a client?")
    revisions_needed: str = Field(description="Specific, actionable feedback and revisions for the writer. Be very critical.")

report_evaluator_agent = Agent(
    name="ReportEvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportEvaluation
)
