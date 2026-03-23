from agents import Agent

from llm import balanced_model_settings, small_model
from schemas import ClarifyingQuestions

INSTRUCTIONS = """You generate exactly 3 clarifying questions for a research request.

Each question should materially improve the later research plan by uncovering:
1. The user's preferred angle or decision they care about most.
2. The expected scope, depth, or audience.
3. Any constraints such as geography, timeline, industry, or comparison criteria.

Keep the questions concise, practical, and non-overlapping."""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model=small_model,
    model_settings=balanced_model_settings,
    output_type=ClarifyingQuestions,
)
