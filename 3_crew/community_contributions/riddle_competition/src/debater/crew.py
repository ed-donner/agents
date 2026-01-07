from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Debate():
    """Debate crew"""


    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def puzzle_maker(self) -> Agent:
        return Agent(
            config=self.agents_config['puzzle_maker'],
            verbose=True
        )

    @agent
    def puzzle_judge(self) -> Agent:
        return Agent(
            config=self.agents_config['puzzle_judge'],
            verbose=True
        )

    @task
    def puzzle_1(self) -> Task:
        return Task(
            config=self.tasks_config['puzzle_1'],
        )

    @task
    def puzzle_2(self) -> Task:
        return Task(
            config=self.tasks_config['puzzle_2'],
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )