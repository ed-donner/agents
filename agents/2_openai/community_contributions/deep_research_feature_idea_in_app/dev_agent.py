from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a technical product assistant. You convert a clarified feature idea into a developer-friendly handoff.\n"
    "Your output should include clear user stories, acceptance criteria, and any relevant implementation notes.\n"
    "Use markdown format, and consider technical feasibility, edge cases, and user experience."
)

class DevHandoff(BaseModel):
    user_stories: list[str] = Field(description="List of user stories (as 'As a..., I want..., so that...').")
    acceptance_criteria: list[str] = Field(description="Acceptance criteria for validating feature completion.")
    dev_notes: str = Field(description="Any technical notes, assumptions, or constraints for engineers.")

dev_agent = Agent(
    name="DevAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=DevHandoff
)
