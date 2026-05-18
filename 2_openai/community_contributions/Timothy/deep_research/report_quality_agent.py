from agents import Agent
from pydantic import BaseModel, Field

class QualityField(BaseModel):
    score: int = Field(description="Score from 1 (worst) to 5 (best)")
    comments: str = Field(description="Brief explanation and suggestions for improvement.")

class ReportQuality(BaseModel):
    bias: QualityField
    completeness: QualityField
    clarity: QualityField

INSTRUCTIONS = (
    "You are a report quality checker. Given a research report, analyze it for bias, completeness, and clarity. "
    "Return your output as a ReportQuality object with three fields: 'bias', 'completeness', and 'clarity'. Each field is a QualityField with a 'score' (1-5) and 'comments'."
)

report_quality_agent = Agent(
    name="ReportQualityAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportQuality,
)