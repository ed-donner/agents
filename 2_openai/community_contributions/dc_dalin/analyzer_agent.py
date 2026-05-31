from agents import Agent
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field

INSTRUCTIONS = (
    "You are a learning expert tasked with analyzing a skill to help someone create a learning roadmap. "
    "Given a skill name, you need to break it down into its fundamental components.\n"
    "First, identify what prerequisites someone needs before starting this skill. These should be "
    "foundational skills or knowledge that are absolutely necessary.\n"
    "Next, identify the core learning areas that make up this skill. Break the skill into 3-6 major "
    "topics that someone needs to master. Be specific and practical.\n"
    "Finally, determine the overall difficulty level: beginner, intermediate, or advanced.\n"
    "Your analysis will be used to plan resources and projects, so be thorough and accurate."
)

class SkillBreakdown(BaseModel):
    prerequisites: list[str] = Field(description="List of prerequisite skills or knowledge needed")
    core_areas: list[str] = Field(description="3-6 core learning areas that make up this skill")
    difficulty: str = Field(description="Overall difficulty: beginner, intermediate, or advanced")

analyzer_agent = Agent(
    name="Analyzer",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SkillBreakdown,
    model_settings=ModelSettings(temperature=0.7, max_tokens=500)
)
