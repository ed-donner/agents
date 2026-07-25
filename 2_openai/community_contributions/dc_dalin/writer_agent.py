from agents import Agent
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field

INSTRUCTIONS = (
    "You are a learning path architect creating comprehensive roadmaps for skill development. "
    "You will be given a skill, its breakdown, available resources, and project ideas. "
    "Your job is to synthesize all this into a cohesive, actionable learning path.\n\n"
    "Create a detailed markdown document with these sections:\n"
    "1. Overview - Brief introduction to the skill and what makes it valuable\n"
    "2. Prerequisites - What someone needs to know first\n"
    "3. Learning Roadmap - Core areas broken down with recommended resources for each\n"
    "4. Hands-On Projects - Project ideas in order of difficulty\n"
    "5. Timeline - Realistic milestones based on hours per week commitment\n\n"
    "The output should be well-structured, detailed, and at least 600 words. "
    "Use markdown formatting with headers, lists, and emphasis where appropriate. "
    "Be encouraging but realistic about time commitments. "
    "The goal is someone reading this can immediately start their learning journey."
)

class LearningPath(BaseModel):
    title: str = Field(description="Title of the learning path")
    content: str = Field(description="Full learning path in markdown format")
    hours: int = Field(description="Estimated total hours needed to complete")

writer_agent = Agent(
    name="Writer",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=LearningPath,
    model_settings=ModelSettings(temperature=0.7, max_tokens=2000)
)
