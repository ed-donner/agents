from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from flow_engineering_team.tools.sandbox_tools import sandbox_tools


@CrewBase
class DesignCrew:
    """Design the app before implementation starts."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_lead"],  # type: ignore[index]
            tools=sandbox_tools,
            verbose=True,
        )

    @agent
    def engineering_editor(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_editor"],  # type: ignore[index]
            tools=sandbox_tools,
            verbose=True,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config["design_task"],  # type: ignore[index]
            output_file="sandbox/design/design_spec.md",
        )

    @task
    def polish_design_task(self) -> Task:
        return Task(
            config=self.tasks_config["polish_design_task"],  # type: ignore[index]
            output_file="sandbox/design/final_design.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
