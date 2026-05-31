from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_QUESTIONS = 3

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of {HOW_MANY_QUESTIONS} questions that will help focus and refine the research. \
    The questions should be specific and focused on the query. \
    They should be open-ended and not lead to a specific answer."
 

class ClarifyingQuestion(BaseModel):
    reason: str = Field(description="Your reasoning for why this question is important to the research and initial query.")
    question: str = Field(description="The question that will be sent to the user to facilitate subsequent research.")


class ClarifyingQuestions(BaseModel):
    clarifiers: list[ClarifyingQuestion] = Field(description="A list of questions that will facilitate better research.")
    
clarify_agent = Agent(
    name="ClarifyAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)



