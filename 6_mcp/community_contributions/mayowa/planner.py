from typing import List

from agents import Agent, Runner
from pydantic import BaseModel, Field


INSTRUCTIONS = f"""You are a helpful research planner.

Your job is to turn a research question/query plus the user's clarifying answers into a focused web research plan.

Rules:
- Generate exactly 5 search queries.
- Prioritize the clarified audience, scope, timeframe, region, and constraints.
- Blend baseline context with more targeted searches.
- Favor search queries that are concrete enough to surface strong sources.
"""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters for the report.")
    query: str = Field(description="The search query to run.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="The ordered list of web searches to perform.")


class Planner:
    def __init__(self, clarifying_questions: List[str], clarifying_answers: List[str]):
        self.clarifying_questions = clarifying_questions
        self.clarifying_answers = clarifying_answers
        self.agent = Agent(
            name="PlannerAgent",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            output_type=WebSearchPlan,
        )

    async def run(self, query: str) -> WebSearchPlan:
        clarification_block = "\n".join(
            [
                f"{index + 1}) Question: {question}\n   Answer: {answer}"
                for index, (question, answer) in enumerate(
                    zip(self.clarifying_questions, self.clarifying_answers, strict=False)
                )
            ]
        )

        result = await Runner.run(
            self.agent,
            f"Research query: {query}\n\nClarifications:\n{clarification_block}",
        )
        return result.final_output_as(WebSearchPlan)
