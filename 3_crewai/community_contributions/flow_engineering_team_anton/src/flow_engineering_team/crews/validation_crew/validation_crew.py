from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from flow_engineering_team.tools.sandbox_tools import sandbox_tools


@CrewBase
class ValidationCrew:
    """Validate the whole app and produce the sign-off report."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def product_owner(self) -> Agent:
        return Agent(
            config=self.agents_config["product_owner"],  # type: ignore[index]
            tools=sandbox_tools,
            verbose=True,
        )

    @agent
    def quality_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config["quality_auditor"],  # type: ignore[index]
            tools=sandbox_tools,
            verbose=True,
        )

    @task
    def integration_review_task(self) -> Task:
        return Task(
            config=self.tasks_config["integration_review_task"],  # type: ignore[index]
            output_file="sandbox/validation/integration_review.md",
        )

    @task
    def signoff_task(self) -> Task:
        return Task(
            config=self.tasks_config["signoff_task"],  # type: ignore[index]
            output_file="sandbox/validation/signoff.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
