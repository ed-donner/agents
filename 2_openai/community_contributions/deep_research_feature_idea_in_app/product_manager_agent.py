from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a product manager assistant AI. You take a proposed feature idea and raise any potential concerns, edge cases, or business clarifications.\n"
    "Then, you rewrite the idea into a clearer, more detailed spec based on the discussion.\n"
    "Be precise, concise, and always consider product feasibility and user impact."
)

class ClarifiedFeature(BaseModel):
    clarified_spec: str = Field(description="A clarified, PM-reviewed version of the feature spec.")
    pm_questions: list[str] = Field(description="Questions or considerations raised during clarification.")

product_manager_agent = Agent(
    name="ProductManagerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifiedFeature
)