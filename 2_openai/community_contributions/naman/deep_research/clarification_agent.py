from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_QUESTIONS = 3

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description=f"A list of {HOW_MANY_QUESTIONS} clarifying questions to better understand the user's research query.")

clarification_agent = Agent(
    name="Clarification Agent",
    instructions=f"You are a clarification agent. You are given a query and you need to come up with {HOW_MANY_QUESTIONS} clarifying questions to better understand the user's intent. Produce {HOW_MANY_QUESTIONS} short, specific questions that narrow scope, audience, or constraints for the given research topic (no web search tools needed).",
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)