from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Debate():
    """Debate crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def proposer(self) -> Agent:
        # Uses gpt-4o-mini to argue FOR the motion
        return Agent(
            config=self.agents_config['proposer'],
            verbose=True
        )

    @agent
    def opposer(self) -> Agent:
        # Uses gpt-4o to argue AGAINST the motion
        # Different model = different debating style!
        return Agent(
            config=self.agents_config['opposer'],
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        # Uses gpt-4o-mini to pick the winner
        return Agent(
            config=self.agents_config['judge'],
            verbose=True
        )

    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config['propose'],
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config['oppose'],
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )