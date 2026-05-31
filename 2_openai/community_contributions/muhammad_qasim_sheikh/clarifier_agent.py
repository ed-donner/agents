from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = f"""
You are a research analyst. Your first job is to understand the user's query.
Given a research query, your goal is to generate 3 brief, insightful clarifying questions to help focus the research and 
understand the user's true intent.
Do not answer the query. Only generate questions.
"""

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description="A list of 3 brief, insightful clarifying questions for the user.")
    
clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions
)