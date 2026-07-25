

from agents import Agent
from pydantic import BaseModel, Field


NUMBER_OF_QUESTIONS = 3

INSTRUCTIONS = f"You are a helpful research assistant. Given a query and previous question and answer (if any), \
    come up with the most important question to ask to clarify the query. \
    Output the question. \
    If the query is already clear or the number of questions asked reachs {NUMBER_OF_QUESTIONS}, output an empty string."

class ClarifyingQuestionItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this question is important to clarify the query.")
    question: str = Field(description="The clarifying question to ask.")

clarifying_agent = Agent(
    name="ClarifyingAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestionItem,
)