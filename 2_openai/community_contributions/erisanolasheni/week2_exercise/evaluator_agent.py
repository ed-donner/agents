from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You review a draft research report against the original brief and clarifications.
Decide if the report is adequate for a professional reader (coverage, accuracy tone, structure).
If adequate, say so briefly. If not, give concrete revision instructions the writer can apply in one pass."""


class EvaluationBrief(BaseModel):
    adequate: bool = Field(description="True if the report is good enough to ship without major gaps.")
    comment: str = Field(description="Short overall assessment.")
    revision_brief: str = Field(
        default="",
        description="If adequate is false, specific fixes; otherwise empty.",
    )


evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluationBrief,
)
