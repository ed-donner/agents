from agents import Agent
from pydantic import BaseModel, Field

class EvaluationResult(BaseModel):
    score: int = Field(description="A score from 1 to 10 evaluating the quality of the research report, where 10 is the best possible score.")
    feedback: str = Field(description="Detailed feedback on the research report, including what was done well and what could be improved.")
    suggestions: list[str] = Field(description="Specific suggestions for how to improve the research report.")
    approved: bool = Field(description="Whether the research report is approved based on the evaluation criteria.")

instructions="""
        You are a research report evaluator.
        You will receive an original query and a generated report.
        Evaluate the report for:
        - Accuracy and relevance to the query
        - Completeness and depth
        - Clarity and structure
        
        Return a score (1-10) where 10 is the best possible score, detailed feedback, suggestions for improvement,
        and whether the report is approved.
    """

evaluator_agent = Agent(
    name = "Evaluator Agent",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=EvaluationResult
)


