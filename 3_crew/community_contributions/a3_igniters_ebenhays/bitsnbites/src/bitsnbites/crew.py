from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool


@CrewBase
class Bitsnbites:
    """Bitsnbites crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def scout(self) -> Agent:
        return Agent(
            config=self.agents_config["scout"],
            verbose=True,
            tools=[SerperDevTool()],
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],
            verbose=True,
            tools=[SerperDevTool()],
        )

    @task
    def scout_task(self) -> Task:
        return Task(config=self.tasks_config["scout_task"])

    @task
    def analyst_task(self) -> Task:
        return Task(config=self.tasks_config["analyst_task"])

    @crew
    def crew(self) -> Crew:
        """Creates the Bitsnbites crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
