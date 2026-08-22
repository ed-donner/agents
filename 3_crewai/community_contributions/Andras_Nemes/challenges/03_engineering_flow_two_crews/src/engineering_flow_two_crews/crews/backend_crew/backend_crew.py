from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class BackendCrew:
    '''A small crew responsible only for the backend implementation.'''

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def backend_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_developer'],  # type: ignore[index]
            verbose=True,
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @task
    def implement_backend(self) -> Task:
        return Task(
            config=self.tasks_config['implement_backend'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
