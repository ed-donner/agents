from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a clarification agent. Your job is to generate a list of 3 clarifying questions "
    "that will help narrow down and better understand a research query. The questions should:\n"
    "1. Explore the user's specific interests and goals\n"
    "2. Identify any constraints or preferences\n"
    "3. Determine the scope and depth of information needed\n"
    "Your questions should be clear, specific, and help guide the research process."
)

class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(description="A list of 3 clarifying questions to better understand the research query")
    reasoning: str = Field(description="Brief explanation of why these questions will help improve the research")

clarify_agent = Agent(
    name="ClarifyAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
) 