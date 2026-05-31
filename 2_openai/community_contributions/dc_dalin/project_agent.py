from agents import Agent
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field

INSTRUCTIONS = (
    "You are a project designer creating hands-on learning projects. "
    "Given a skill and its core learning areas, design 3-5 project ideas that help someone "
    "learn by doing.\n"
    "Start with a simple beginner-friendly project and progress to more complex ones. "
    "Each project should:\n"
    "- Have a clear, specific goal\n"
    "- Build real skills related to the core areas\n"
    "- Be completable within a reasonable timeframe\n"
    "- Have tangible deliverables\n"
    "Projects should increase in difficulty, with later projects building on earlier ones. "
    "Be creative but practical. Focus on projects that someone could actually build."
)

class ProjectIdea(BaseModel):
    name: str = Field(description="Project name")
    description: str = Field(description="What the project involves and what will be learned")
    difficulty: str = Field(description="beginner, intermediate, or advanced")

class Projects(BaseModel):
    projects: list[ProjectIdea] = Field(description="List of 3-5 project ideas in order of difficulty")

project_agent = Agent(
    name="Projects",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=Projects,
    model_settings=ModelSettings(temperature=0.8, max_tokens=600)
)
