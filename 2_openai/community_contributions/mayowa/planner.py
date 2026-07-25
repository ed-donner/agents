## Planner Agent
from agents import Agent, Runner
from pydantic import BaseModel, Field
from typing import List


INSTRUCTIONS = """You are a helpful research assistant. Given a query, come up with a set of web searches to perform to best answer the query.
Here are the clarifying questions and answers to help you refine the query.

Clarifications:
1) Question: {questions[0]}
   Answer: {answers[0]}
2) Question: {questions[1]}
   Answer: {answers[1]}
3) Question: {questions[2]}
   Answer: {answers[2]}

Instruction:
- Generate 5 web searches.
- Prioritize the clarified audience/scope/timeframe/region.
- Avoid broad generic searches unless needed for baseline context."""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")


class Planner:
    def __init__(self, clarifying_questions: List[str], clarifying_answers: List[str]):
        self.clarifying_questions = clarifying_questions
        self.clarifying_answers = clarifying_answers
        self.agent = Agent(
            name="PlannerAgent",
            instructions=INSTRUCTIONS.format(questions=self.clarifying_questions, answers=self.clarifying_answers),
            model="gpt-4o-mini",
            output_type=WebSearchPlan,
        )

    async def run(self, query):
        """
        Run the planner agent.
        """

        print("Planning searches...")
        result = await Runner.run(self.agent, f"Query: {query}")
        print(f"Will perform {len(result.final_output.searches)} searches")

        return result.final_output_as(WebSearchPlan)

