from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = f"""
You are a senior research analyst. You will be given the original research query and a list of search result summaries.
Your job is to determine if these summaries are sufficient, relevant, and comprehensive enough to write a 1000-word report.
You must identify any gaps or missing topics. Be critical, a "False" rating will trigger a new, better search.
"""

class SearchEvaluation(BaseModel):
    is_sufficient: bool = Field(description="Are the search results high-quality and comprehensive enough to write a 1000-word report?")
    missing_topics: list[str] = Field(description="A list of specific topics that are missing or need more detail.")
    feedback: str = Field(description="Your 1-2 sentence reasoning for your decision.")

search_evaluator_agent = Agent(
    name="SearchEvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SearchEvaluation
)