from pydantic import BaseModel, Field
from agents import Agent


class EvaluationResult(BaseModel):
    score: int = Field(
        ge=1,
        le=10,
        description="Overall quality and completeness of the report vs the research query (1=very poor, 10=excellent).",
    )
    missing_topics: list[str] = Field(
        description="Important angles, subtopics, or evidence gaps that are missing or underdeveloped.",
    )
    suggested_improvements: str = Field(
        description="Concrete suggestions to strengthen the report (structure, depth, sourcing, balance).",
    )
    should_continue_research: bool = Field(
        description="True if more web research is needed before the report can be considered adequate.",
    )


INSTRUCTIONS = (
    "You are an expert research editor. You receive the original user research query (and any clarifications) "
    "and a draft research report in markdown.\n"
    "Critically assess coverage, accuracy signals, depth, balance of perspectives, and use of evidence. "
    "List missing topics that warrant additional search. Suggest specific improvements.\n"
    "Set should_continue_research to true if score is below 7 or if major factual gaps or missing sections remain "
    "that web research could plausibly fix. Set it to false if the report is already strong for the query."
)

evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluationResult,
)
