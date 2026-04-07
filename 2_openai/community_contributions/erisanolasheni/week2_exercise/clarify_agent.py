from agents import Agent
from schemas import ClarifyingQuestions

INSTRUCTIONS = """You help scope deep-research requests. Given a user's topic, produce exactly three
short clarifying questions that will sharpen the research plan (e.g. geography, timeframe, audience,
technical depth, or success criteria). Questions must be answerable in a sentence each by the user."""

clarify_agent = Agent(
    name="ClarifyAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)
