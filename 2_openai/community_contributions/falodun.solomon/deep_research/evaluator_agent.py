from pydantic import BaseModel, Field
from agents import Agent

class EvaluationResult(BaseModel):
    quality_score: int = Field(description="0-10 quality score")
    is_sufficient: bool
    missing_areas: list[str]
    recommended_actions: list[str]
    new_search_queries: list[str]

INSTRUCTIONS = """
You are a strict research evaluator.

Evaluate the report based on:
- Completeness
- Depth
- Clarity
- Alignment with query

Return:
- quality_score (0-10)
- is_sufficient (true if >=8)
- missing areas
- recommended actions:
    ["more_search", "refine_query", "ask_user"]
- new search queries if needed
"""

evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluationResult,
)
