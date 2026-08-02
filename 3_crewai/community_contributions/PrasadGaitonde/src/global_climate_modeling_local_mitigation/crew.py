from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class GlobalClimateModelingLocalMitigation():
    """GlobalClimateModelingLocalMitigation crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def team_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['team_lead'], # type: ignore[index]
            verbose=True
        )

    @agent
    def data_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['data_engineer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def climate_modeler(self) -> Agent:
        return Agent(
            config=self.agents_config['climate_modeler'], # type: ignore[index]
            verbose=True
        )

    @agent
    def impact_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['impact_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def solution_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['solution_architect'], # type: ignore[index]
            verbose=True
        )

    @task
    def data_ingestion_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_ingestion_task'], # type: ignore[index]
        )

    @task
    def climate_modeling_task(self) -> Task:
        return Task(
            config=self.tasks_config['climate_modeling_task'], # type: ignore[index]
        )

    @task
    def impact_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config['impact_assessment_task'], # type: ignore[index]
        )

    @task
    def solution_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['solution_design_task'], # type: ignore[index]
        )

    @task
    def final_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_review_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the GlobalClimateModelingLocalMitigation crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
