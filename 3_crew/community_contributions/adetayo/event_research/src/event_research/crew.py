from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from event_research.tools.custom_tool import DatabaseTool

@CrewBase
class EventResearch():
    """EventResearch crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True
        )

    @agent
    def data_entry_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_entry_analyst'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def data_entry_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_entry_task'], # type: ignore[index]
            output_file='report.md',
            tools=[DatabaseTool()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EventResearch crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
