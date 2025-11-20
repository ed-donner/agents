# evaluator_agent.py
from pydantic import BaseModel, Field
from typing import List
from agents import Agent
from models import llama3_model  # your shared instance

class EvaluationFeedback(BaseModel):
    suggestions: List[str] = Field(description="Suggestions to improve the research report")

INSTRUCTIONS = """
You are a critical reviewer. Evaluate the quality, clarity, completeness, and relevance of the research report.
Identify any gaps, factual inconsistencies, or vague sections. Provide concise suggestions to improve it.
"""

evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model=llama3_model,
    output_type=EvaluationFeedback,
)
