from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List


@CrewBase
class HaliCrew():
    """HALI — HPV Awareness & Learning Initiative crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def myth_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['myth_researcher'],
            verbose=True
        )

    @agent
    def myth_buster(self) -> Agent:
        return Agent(
            config=self.agents_config['myth_buster'],
            verbose=True
        )

    @agent
    def community_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['community_writer'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
        )

    @task
    def rebuttal_task(self) -> Task:
        return Task(
            config=self.tasks_config['rebuttal_task'],
        )

    @task
    def community_message_task(self) -> Task:
        return Task(
            config=self.tasks_config['community_message_task'],
            output_file='community_message.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
