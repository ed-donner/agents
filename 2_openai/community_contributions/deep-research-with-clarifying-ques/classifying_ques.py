from pydantic import BaseModel, Field
from agents import Agent


class ClassifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description=(
            "Exactly three classifying questions that clarify the user's intent and constraints "
            "in a way that would materially change what we search for."
        )
    )


INSTRUCTIONS = """
You are a research assistant. Given a research query, generate EXACTLY 3 classifying questions.

These are NOT generic filler questions; each should capture a key dimension that affects search strategy, like:
- scope/breadth vs depth, and what “done” looks like
- audience/context (beginner vs expert, industry, use case)
- constraints (timeframe, geography, budget, tech stack, regulations)

Rules:
- Output exactly 3 questions in a list (no extra text).
- Prefer questions that can be answered in 1-2 sentences.
- Avoid yes/no questions unless unavoidable.
"""


classifier_agent = Agent(
    name="ClassifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClassifyingQuestions,
)
