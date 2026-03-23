from agents import Agent

from llm import balanced_model_settings, small_model
from schemas import CoverageAssessment

INSTRUCTIONS = """You evaluate whether the accumulated research is sufficient to write the final report.

Be conservative. Set `is_complete` to true only when the evidence covers:
- the user's clarified objective
- the major subtopics needed for a credible answer
- important tradeoffs, comparisons, or constraints

If coverage is incomplete, list concrete remaining gaps and describe the best focus for the next
research round. Avoid generic advice."""

evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model=small_model,
    model_settings=balanced_model_settings,
    output_type=CoverageAssessment,
)
