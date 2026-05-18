from pydantic import BaseModel, Field
from agents import Agent


INSTRUCTIONS = (
    "You are a research query refinement specialist. You will receive an original research query "
    "along with 3 clarifying questions and the user's answers to those questions. "
    "Your job is to synthesize this information into a refined, more specific research query and "
    "a list of key focus areas that should guide the research.\n\n"
    "The refined query should:\n"
    "- Incorporate all relevant details from the user's answers\n"
    "- Be specific and unambiguous\n"
    "- Preserve the user's original intent while adding the clarified scope\n\n"
    "The key focus areas should be 3-5 distinct themes or angles to investigate."
)


class RefinedQuery(BaseModel):
    refined_query: str = Field(
        description="A refined, more specific version of the original query incorporating the user's clarifications."
    )
    key_focus_areas: list[str] = Field(
        description="3-5 key focus areas that should guide the research."
    )


query_refiner_agent = Agent(
    name="QueryRefinerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini",
    output_type=RefinedQuery,
)
