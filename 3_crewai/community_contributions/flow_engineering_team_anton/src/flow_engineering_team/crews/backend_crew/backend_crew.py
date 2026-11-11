from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from flow_engineering_team.tools.sandbox_tools import sandbox_tools


@CrewBase
class BackendCrew:
    """Build backend artifacts for the app."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],  # type: ignore[index]
            tools=sandbox_tools,
            verbose=True,
        )

    @agent
    def backend_tester(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_tester"],  # type: ignore[index]
            tools=sandbox_tools,
            verbose=True,
        )

    @task
    def backend_implementation_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_implementation_task"],  # type: ignore[index]
            output_file="sandbox/backend/backend_summary.md",
        )

    @task
    def backend_test_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_test_task"],  # type: ignore[index]
            output_file="sandbox/backend/backend_test_report.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
