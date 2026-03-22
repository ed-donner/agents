from agents import Agent
from pydantic import BaseModel


class EvaluationResult(BaseModel):
    score: int
    passes: bool
    feedback: str


EVALUATOR_PROMPT = """
You are a research report evaluator. Given an original query and a written report, 
evaluate the report on:
- Does it fully answer the query?
- Is the structure clear and logical?
- Are claims supported by evidence?
- Are there any obvious gaps?

Score it 1-10. Set passes=True if score >= 7.
Provide specific, actionable feedback for improvement if it fails.
"""

evaluator_agent = Agent(
    name="Evaluator Agent",
    instructions=EVALUATOR_PROMPT,
    output_type=EvaluationResult,
    model="gpt-4o",
)

evaluator_tool = evaluator_agent.as_tool(
    tool_name="evaluate_report",
    tool_description="Evaluates a written research report against the original query. Returns a score, pass/fail, and feedback for improvement.",
)