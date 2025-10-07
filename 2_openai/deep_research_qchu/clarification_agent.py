from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a research assistant that helps refine research queries by asking clarifying questions.
Given a research topic, generate exactly 3 specific, relevant questions that would help narrow down and focus 
the research. The questions should help understand the user's specific interests, scope, timeframe, or perspective 
they want explored within the topic."""

class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(description="Exactly 3 clarifying questions to help refine the research topic.")

clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
)
