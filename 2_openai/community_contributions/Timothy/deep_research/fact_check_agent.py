from agents import Agent
from pydantic import BaseModel, Field
from typing import List, Literal

class FactCheckItem(BaseModel):
    claim: str = Field(description="The factual claim extracted from the report.")
    status: Literal['supported', 'contradicted', 'unverifiable'] = Field(description="Verification status.")
    justification: str = Field(description="Brief justification with evidence or reasoning.")

INSTRUCTIONS = (
    "You are a fact-checking agent. Given a research report, extract all factual claims and verify them using web search. "
    "Return your output as a list of FactCheckItem objects, each with: 'claim', 'status' (supported, contradicted, unverifiable), and 'justification'."
)

fact_check_agent = Agent(
    name="FactCheckAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=List[FactCheckItem],
)