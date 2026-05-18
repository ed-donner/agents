from typing import List
from pydantic import BaseModel, Field
from agents import Agent
from helper import AGENT_MODEL

NUMBER_OF_CLARIFYING_QUESTIONS = 3

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, refine it with exactly {NUMBER_OF_CLARIFYING_QUESTIONS} \
clarifying questions so that the web search could be improved and the searches are more specific and focused. Return the \
list of clarifying questions and the refined query as your final output."


class RefinedQuery(BaseModel):
    clarifying_questions: List[str] = Field(description="The list of clarifying questions to refine the query with.")
    refined_query: str = Field(description="The refined query.")


refine_query_agent = Agent(
    name="Refine Query Agent",
    instructions=INSTRUCTIONS,
    model=AGENT_MODEL,
    output_type=RefinedQuery,
)
