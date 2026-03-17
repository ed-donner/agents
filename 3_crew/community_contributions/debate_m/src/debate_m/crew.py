from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class DebateM():
    """DebateM crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def debater_propose(self) -> Agent:
        return Agent(config=self.agents_config['debater_propose'], verbose=True)

    @agent
    def debater_oppose(self) -> Agent:
        return Agent(config=self.agents_config['debater_oppose'], verbose=True)

    @agent
    def debater_piglatin(self) -> Agent:
        return Agent(config=self.agents_config['debater_piglatin'], verbose=True)

    @agent
    def debater_choice(self) -> Agent:
        return Agent(config=self.agents_config['debater_choice'], verbose=True)

    @agent
    def judge(self) -> Agent:
        return Agent(config=self.agents_config['judge'], verbose=True)

    # ---------------

    @task
    def propose(self) -> Task:
        return Task(config=self.tasks_config['propose'])

    @task
    def oppose(self) -> Task:
        return Task(config=self.tasks_config['oppose'])

    @task
    def debate_piglatin(self) -> Task:
        return Task(config=self.tasks_config['debate_piglatin'])

    @task
    def debate_choice(self) -> Task:
        return Task(config=self.tasks_config['debate_choice'])

    @task
    def decide(self) -> Task:
        return Task(config=self.tasks_config['decide'])

    # ------

    @crew
    def crew(self) -> Crew:
        """Creates the DebateM crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
