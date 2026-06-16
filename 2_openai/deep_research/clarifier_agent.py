from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a research assistant. Given a user's research query, generate exactly 3 clarifying questions
that will help focus and deepen the research. Questions should:
- Disambiguate scope (e.g. time period, region, audience)
- Uncover what "good" looks like (e.g. depth, format, use case)
- Surface constraints or priorities the user might have

Return exactly 3 short, specific questions. Do not answer them."""


class ClarificationData(BaseModel):
    questions: list[str] = Field(
        description="Exactly 3 clarifying questions to refine the research query.",
    )


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationData,
)
