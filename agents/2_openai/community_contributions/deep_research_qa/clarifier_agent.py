from typing import List
from pydantic import BaseModel
from agents import Agent

class ClarificationData(BaseModel):
    questions: List[str]

CLARIFY_INSTRUCTIONS = """
You are a Research Clarifier. Given a user's research query, generate exactly 3 clarifying questions 
that will help focus and refine the research. These questions should help understand:
1. The specific aspect or angle they want to focus on
2. The depth or scope of research needed
3. The intended use or audience for the research

Return your response as JSON matching the ClarificationData model with exactly 3 questions.
"""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=CLARIFY_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationData,
) 