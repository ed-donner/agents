from pydantic import BaseModel, Field
from agents import Agent


class GapItem(BaseModel):
    topic: str = Field(description="The topic or aspect that is missing or underdeveloped.")
    severity: str = Field(description="How critical this gap is: 'high', 'medium', or 'low'.")
    suggested_searches: list[str] = Field(
        description="1-3 specific web search queries that would help fill this gap."
    )


class Evaluation(BaseModel):
    coverage_score: int = Field(
        description="How well the report covers the query, 1-10.",
        ge=1, le=10,
    )
    depth_score: int = Field(
        description="How deep and detailed the analysis is, 1-10.",
        ge=1, le=10,
    )
    coherence_score: int = Field(
        description="How well-structured and logically flowing the report is, 1-10.",
        ge=1, le=10,
    )
    overall_score: int = Field(
        description="Overall quality score, 1-10.",
        ge=1, le=10,
    )
    strengths: list[str] = Field(
        description="2-4 things the report does well."
    )
    gaps: list[GapItem] = Field(
        description="Identified gaps or missing perspectives. Empty list if none."
    )
    verdict: str = Field(
        description="One of: 'pass' (report is good enough), 'revise' (gaps should be filled)."
    )
    summary: str = Field(
        description="A 2-3 sentence overall assessment."
    )


INSTRUCTIONS = (
    "You are a senior research evaluator. You will receive:\n"
    "- The original research query\n"
    "- Key focus areas (if any)\n"
    "- The search results that were used\n"
    "- The generated report\n\n"
    "Your job is to critically evaluate the report and identify gaps. Assess:\n"
    "1. **Coverage**: Does the report address all aspects of the query and focus areas?\n"
    "2. **Depth**: Is each topic covered with sufficient detail and nuance?\n"
    "3. **Coherence**: Is the report well-structured, logically flowing, and readable?\n"
    "4. **Missing perspectives**: Are there important viewpoints, counterarguments, or angles not explored?\n"
    "5. **Factual grounding**: Are claims supported by the provided search results?\n\n"
    "Be rigorous but fair. Only flag gaps that materially affect the report's usefulness.\n"
    "Set verdict to 'pass' if the overall score is 7+ and there are no high-severity gaps.\n"
    "Set verdict to 'revise' if there are high-severity gaps or the overall score is below 7.\n"
    "For each gap, provide specific search queries that would help fill it."
)


evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini",
    output_type=Evaluation,
)
