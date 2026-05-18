from agents import Agent
from pydantic import BaseModel, Field
from typing import List

class FollowupQuestions(BaseModel):
    questions: List[str] = Field(description="A list of follow-up questions.")

INSTRUCTIONS = (
    "You are a follow-up question generator. Given a research report and the original query, suggest 3-5 relevant follow-up questions that would help deepen or clarify the research. "
    "Return your output as a FollowupQuestions object with a 'questions' field (list of strings)."
)

followup_question_agent = Agent(
    name="FollowupQuestionAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=FollowupQuestions,
)