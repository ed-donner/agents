from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SKILLS = 3

INSTRUCTIONS = (
    f"You are an expert learning path architect. Given a learning goal plus learner constraints, "
    f"break it down into exactly {HOW_MANY_SKILLS} core skills or knowledge areas required to achieve that goal. "
    "Order them logically from foundational to advanced. For each skill, provide a brief reason why it is "
    "essential, a suggested time allocation in weeks, and 2-3 concrete subskills. "
    "You must adapt pacing and scope based on available hours per week and prior experience. "
    "If the learner has a low budget, prefer a plan that can be achieved mostly with free or low-cost resources. "
    "Ensure the ordering makes sense for progressive skill building."
)


class SubSkill(BaseModel):
    name: str = Field(description="Name of the subskill.")
    description: str = Field(description="One sentence describing what this subskill covers.")


class SkillItem(BaseModel):
    name: str = Field(description="Name of the skill or knowledge area.")
    reason: str = Field(description="Why this skill is essential to achieving the goal.")
    week_start: int = Field(description="The week in which study of this skill should begin.")
    week_end: int = Field(description="The week in which study of this skill should end.")
    subskills: list[SubSkill] = Field(description="2-3 concrete subskills under this skill.")


class LearningPlan(BaseModel):
    goal_summary: str = Field(description="A one-sentence restatement of the learning goal.")
    total_weeks: int = Field(description="Total number of weeks in the learning plan.")
    skills: list[SkillItem] = Field(description="Ordered list of skills to learn.")
    final_project_idea: str = Field(description="A capstone project idea that ties all skills together.")


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=LearningPlan,
)
