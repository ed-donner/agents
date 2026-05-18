from pydantic import BaseModel, Field
from agents import Agent


INSTRUCTIONS = (
    "You are a research planning assistant. Given a user's research query, generate exactly 3 "
    "clarifying questions that will help narrow down the scope and improve the quality of the research. "
    "Focus on identifying:\n"
    "- Ambiguities in the query (e.g., which aspect, time period, geographic region)\n"
    "- The user's intent (e.g., academic overview vs practical how-to vs comparison)\n"
    "- Unstated preferences (e.g., depth vs breadth, specific sub-topics of interest)\n"
    "Each question should be concise and directly actionable."
)


class ClarifyingQuestion(BaseModel):
    question: str = Field(description="A clarifying question to ask the user.")
    why: str = Field(description="Why this question helps narrow or improve the research.")


class ClarifyingQuestions(BaseModel):
    questions: list[ClarifyingQuestion] = Field(
        description="Exactly 3 clarifying questions for the user's research query."
    )


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini",
    output_type=ClarifyingQuestions,
)
