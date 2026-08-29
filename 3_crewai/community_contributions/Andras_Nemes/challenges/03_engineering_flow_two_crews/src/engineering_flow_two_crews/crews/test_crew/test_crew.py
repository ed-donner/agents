from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class TestCrew:
    '''A small crew responsible only for independent contract tests.'''

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],  # type: ignore[index]
            verbose=True,
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @task
    def write_unit_tests(self) -> Task:
        return Task(
            config=self.tasks_config['write_unit_tests'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
