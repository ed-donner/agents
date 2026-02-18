from pydantic import BaseModel, Field
from agents import Agent


INSTRUCTIONS = """You are a research clarification assistant. Given a research query, generate exactly 3 
clarifying questions that would help narrow down and improve the research.

Your questions should help understand:
1. The user's specific intent and what angle they care most about
2. The desired scope and depth (broad overview vs. deep dive into a niche)
3. Any particular constraints, time periods, or domains to focus on

Keep each question concise and directly useful for refining search strategy."""


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly 3 clarifying questions to better understand the research query.",
        min_length=3,
        max_length=3,
    )


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)
