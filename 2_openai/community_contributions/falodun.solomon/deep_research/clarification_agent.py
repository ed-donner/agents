from pydantic import BaseModel, Field
from agents import Agent

class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(description="Exactly 3 clarifying questions", min_items=3, max_items=3)

INSTRUCTIONS = """
You are a research assistant.

Given a user query, generate exactly 3 high-quality clarifying questions that:
- Reduce ambiguity
- Help narrow scope
- Improve research quality

Do NOT answer the query.
Only return questions.
"""

clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
)