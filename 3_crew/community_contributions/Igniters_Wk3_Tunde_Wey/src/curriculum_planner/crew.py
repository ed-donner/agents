from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field


class CurriculumArchitectOutput(BaseModel):
    """Structured handoff from strategist to the rest of the crew."""

    learning_spec: str = Field(
        ...,
        description="Full specification: audience, prior knowledge, outcomes, constraints, and success criteria.",
    )
    course_title: str = Field(
        ...,
        description="Short working title for the course or module.",
    )
    delivery_context: str = Field(
        ...,
        description="Format and time: e.g. blended, hours per week, sync vs async, tools allowed.",
    )


@CrewBase
class CurriculumPlannerCrew:
    """Sequential curriculum crew."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def curriculum_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["curriculum_strategist"],
            verbose=True,
        )

    @agent
    def instructional_designer(self) -> Agent:
        return Agent(
            config=self.agents_config["instructional_designer"],
            verbose=True,
        )

    @agent
    def lesson_developer(self) -> Agent:
        return Agent(
            config=self.agents_config["lesson_developer"],
            verbose=True,
        )

    @agent
    def stakeholder_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["stakeholder_writer"],
            verbose=True,
        )

    @agent
    def assessment_designer(self) -> Agent:
        return Agent(
            config=self.agents_config["assessment_designer"],
            verbose=True,
        )

    @task
    def strategist_task(self) -> Task:
        return Task(
            config=self.tasks_config["strategist_task"],
            output_pydantic=CurriculumArchitectOutput,
        )

    @task
    def syllabus_task(self) -> Task:
        return Task(
            config=self.tasks_config["syllabus_task"],
        )

    @task
    def lesson_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config["lesson_plan_task"],
        )

    @task
    def stakeholder_task(self) -> Task:
        return Task(
            config=self.tasks_config["stakeholder_task"],
        )

    @task
    def assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["assessment_task"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
