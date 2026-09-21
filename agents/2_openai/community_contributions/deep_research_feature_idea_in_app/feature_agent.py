from pydantic import BaseModel, Field
from agents import Agent 

INSTRUCTIONS = (
    "You are a product ideation expert. Given a user problem, suggest a concrete product feature.\n"
    "Include rationale, business value, and potential risk. Keep it realistic and impactful."
)

class FeatureIdea(BaseModel):
    title: str = Field(description="Feature name or label")
    description: str = Field(description="What the feature does and why it's valuable")
    risks: list[str] = Field(description="Any potential downsides, technical challenges, or UX concerns")

feature_agent = Agent(
    name="FeatureAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=FeatureIdea
)