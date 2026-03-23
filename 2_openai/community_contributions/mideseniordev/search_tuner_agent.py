from agents import Agent
from pydantic import BaseModel, Field

from config import DEFAULT_MODEL

INSTRUCTIONS = """
You tune a research strategy using:
1) the original query,
2) answers to 3 clarifying questions.

Return a concise research brief that controls planning depth and search budget.
If some answers are missing, infer safe defaults.
"""


class ResearchBrief(BaseModel):
    refined_query: str = Field(description="Refined research query with constraints integrated.")
    output_expectations: str = Field(description="Expected report style, sections, and citation requirements.")
    allowed_tools: str = Field(description="Tools/search constraints to respect during execution.")
    evaluation_expectations: str = Field(description="How output should be validated or demonstrated.")
    search_budget: int = Field(description="Number of searches to plan and execute.")
    focus_areas: list[str] = Field(description="Subtopics that must be covered.")
    avoid_areas: list[str] = Field(description="Topics or sources to avoid if specified.")


search_tuner_agent = Agent(
    name="SearchTunerAgent",
    instructions=INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=ResearchBrief,
)
