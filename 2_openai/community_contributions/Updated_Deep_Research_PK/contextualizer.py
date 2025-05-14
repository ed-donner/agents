from pydantic import BaseModel
from agents import Agent

INSTRUCTIONS = (
    "You are an expert at adding context to user queries, based on thier answers to some clarifying questions.\n" 
    "You will be provided with the original query, the user's answer to that query, the clarifying questions, the purpose of each clarifying question and the user's answer to each clarifying question.\n"
    "You need to generate a contextualized query that incorporates the user's answers to the clarifying questions.\n"
    "The contextualized query should not be a simple concatenation of the user's answers.\n"
    "The contextualized query should accurately reflect the user's intent and should be "
    "relevant to the original query.\n"
    "The contextualized query should be a maximum of 5 sentences long.\n"
)


class ContextualizedQuestions(BaseModel):
    contextualized_query: str
    """A query that has been contextualized based on the clarifying questions asked to the user."""

contextualizing_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ContextualizedQuestions,
)