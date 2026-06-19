from pydantic import BaseModel
from agents import Agent

INSTRUCTIONS = """You are a research query analyzer. Your job is to evaluate if a research query contains enough specific information to conduct thorough research.
If the query is too vague or broad, you should generate 3 clarifying questions that would help narrow down the research scope.
If the query is specific enough, you should indicate that no clarification is needed."""

class QueryAnalysis(BaseModel):
    needs_clarification: bool
    """Whether the query needs clarification or not"""
    
    clarifying_questions: list[str]
    """List of up to 3 clarifying questions if needed, empty list if not needed"""
    
    reasoning: str
    """Explanation of why the query needs or doesn't need clarification"""

question_refiner_agent = Agent(
    name="QuestionRefinerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=QueryAnalysis,
) 