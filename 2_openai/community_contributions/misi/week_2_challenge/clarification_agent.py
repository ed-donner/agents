from pydantic import BaseModel, Field
from agents import Agent


class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly 3 concise clarification questions for the user."
    )


class RefinedQuery(BaseModel):
    refined_query: str = Field(
        description="A single refined research query that combines the user's original query and clarification answers."
    )


QUESTION_INSTRUCTIONS = """
You are a helpful research assistant.
Given a user's initial research topic, ask exactly 3 concise clarification questions that will
improve the quality and focus of later web research.
The questions should uncover the user's goals, constraints, scope, preferences, timeframe,
region, audience, or desired output where relevant.
Return only the questions.
"""


REFINEMENT_INSTRUCTIONS = """
You are a helpful research assistant.
You will receive:
1. The user's original query
2. Three clarification questions
3. The user's three answers

Synthesize them into one refined research query for downstream search planning.
Preserve the user's intent, add useful constraints from the answers, and make the query specific
enough to guide strong web research.
Return only the refined query.
"""


clarification_agent = Agent(
    name="Clarification agent",
    instructions=QUESTION_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
)


refinement_agent = Agent(
    name="Refinement agent",
    instructions=REFINEMENT_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=RefinedQuery,
)
