from pydantic import BaseModel, Field
from agents import Agent
from dotenv import load_dotenv
import os

load_dotenv(override=True)
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")

INSTRUCTIONS = """
You are a meticulous research quality evaluator. You are given the user's original query, the
clarifying questions together with the user's answers, and the search summaries gathered so far.
Judge whether the summaries genuinely address what the user asked for, paying special attention to
the clarifications (scope, audience, time frame, depth, focus).
If anything important is missing or off-target relative to the clarifications, set aligned to false
and give specific, actionable feedback describing what additional searches are needed.
Only set aligned to true when the results truly satisfy the query and the clarifications.
"""


class EvaluationResult(BaseModel):
    aligned: bool = Field(
        description="True only if the search results adequately satisfy the query and the user's clarifications."
    )
    feedback: str = Field(
        description="Specific, actionable feedback on what is missing or misaligned, to guide another round of searching."
    )


evaluator_agent = Agent(name="Evaluator Agent", instructions=INSTRUCTIONS, model=MODEL_NAME, output_type=EvaluationResult)
