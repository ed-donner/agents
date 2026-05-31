import asyncio
from pathlib import Path

from pydantic import BaseModel, Field
from agents import Runner, trace, gen_trace_id

from planner_agent import planner_agent, LearningPlan, SkillItem
from search_agent import search_agent
from writer_agent import writer_agent, RoadmapData
from delivery_agent import delivery_agent


class UserProfile(BaseModel):
    available_hours_per_week: int = Field(description="How many hours per week the learner can study.")
    budget: str = Field(description="Budget level for paid learning resources.")
    prior_experience: str = Field(description="Learner's prior experience level.")
    preferred_learning_style: str = Field(description="Preferred learning style.")
    delivery_target: str = Field(description="Where the roadmap should be delivered.")
    export_format: str = Field(description="Preferred export format for the roadmap.")


class LearningManager:
    async def run(self, goal: str, profile: UserProfile):
        trace_id = gen_trace_id()
        with trace("Learning Path trace", trace_id=trace_id):
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print(f"View trace: {trace_url}")
            yield f"View trace: {trace_url}\n"

            yield "Profile captured\n"

            learning_plan = await self.plan_skills(goal, profile)
            yield f"Skills planned — {len(learning_plan.skills)} skills identified, searching for resources...\n"

            resource_map = await self.gather_resources(learning_plan, profile)
            yield "Resources gathered, writing your roadmap...\n"

            roadmap = await self.write_roadmap(goal, profile, learning_plan, resource_map)
            yield "Roadmap written, preparing delivery package...\n"

            delivery_summary = await self.deliver(goal, profile, roadmap)
            yield "Delivery completed\n"

            yield roadmap.markdown_roadmap
            yield "\n\n---\n\n"
            yield delivery_summary

    async def plan_skills(self, goal: str, profile: UserProfile) -> LearningPlan:
        result = await Runner.run(
            planner_agent,
            (
                f"Learning goal: {goal}\n"
                f"Available hours/week: {profile.available_hours_per_week}\n"
                f"Budget: {profile.budget}\n"
                f"Prior experience: {profile.prior_experience}\n"
                f"Preferred learning style: {profile.preferred_learning_style}\n"
            ),
        )
        return result.final_output_as(LearningPlan)

    async def gather_resources(self, plan: LearningPlan, profile: UserProfile) -> dict[str, str]:
        tasks = {
            skill.name: asyncio.create_task(self.search_for_skill(skill, profile))
            for skill in plan.skills
        }
        results: dict[str, str] = {}
        for name, task in tasks.items():
            result = await task
            if result:
                results[name] = result
        return results

    async def search_for_skill(self, skill: SkillItem, profile: UserProfile) -> str | None:
        subskill_names = ", ".join(s.name for s in skill.subskills)
        query = (
            f"Skill: {skill.name}\n"
            f"Subskills: {subskill_names}\n"
            f"Learner budget: {profile.budget}\n"
            f"Prior experience: {profile.prior_experience}\n"
            f"Preferred learning style: {profile.preferred_learning_style}\n"
            f"Available hours/week: {profile.available_hours_per_week}\n"
            f"Find the best courses, documentation, and a hands-on project idea for this skill."
        )
        try:
            result = await Runner.run(search_agent, query)
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed for {skill.name}: {e}")
            return None

    async def write_roadmap(
        self,
        goal: str,
        profile: UserProfile,
        plan: LearningPlan,
        resource_map: dict[str, str],
    ) -> RoadmapData:
        skills_block = ""
        for skill in plan.skills:
            resources = resource_map.get(skill.name, "No resources found.")
            subskills = "\n".join(f"  - {s.name}: {s.description}" for s in skill.subskills)
            skills_block += (
                f"\n### {skill.name} (Weeks {skill.week_start}-{skill.week_end})\n"
                f"Why it matters: {skill.reason}\n"
                f"Subskills:\n{subskills}\n"
                f"Resources:\n{resources}\n"
            )

        writer_input = (
            f"Goal: {goal}\n"
            f"Available hours/week: {profile.available_hours_per_week}\n"
            f"Budget: {profile.budget}\n"
            f"Prior experience: {profile.prior_experience}\n"
            f"Preferred learning style: {profile.preferred_learning_style}\n"
            f"Delivery target: {profile.delivery_target}\n"
            f"Export format: {profile.export_format}\n"
            f"Goal summary: {plan.goal_summary}\n"
            f"Total duration: {plan.total_weeks} weeks\n"
            f"Capstone project idea: {plan.final_project_idea}\n"
            f"\nSkill breakdown with resources:\n{skills_block}"
        )

        result = await Runner.run(writer_agent, writer_input)
        return result.final_output_as(RoadmapData)

    async def deliver(self, goal: str, profile: UserProfile, roadmap: RoadmapData) -> str:
        output_dir = Path("generated_roadmaps")
        output_dir.mkdir(exist_ok=True)

        preferred_format = profile.export_format
        if profile.delivery_target == "Notion" and preferred_format == "DOCX":
            preferred_format = "Markdown"
        if profile.delivery_target == "Google Sheets" and preferred_format != "CSV":
            preferred_format = "CSV"

        delivery_input = (
            f"Goal: {goal}\n"
            f"Delivery target: {profile.delivery_target}\n"
            f"Export format: {preferred_format}\n"
            f"Output directory: {output_dir.resolve()}\n\n"
            f"Roadmap markdown:\n{roadmap.markdown_roadmap}"
        )

        result = await Runner.run(delivery_agent, delivery_input)
        return str(result.final_output)
