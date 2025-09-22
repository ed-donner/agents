from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class Storytellingbattle():
    """Storytellingbattle crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    @agent
    def storyteller(self) -> Agent:
        return Agent(
            config=self.agents_config['storyteller'],
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],
            verbose=True
        )

    @task
    def contestant1(self) -> Task:
        return Task(
            config=self.tasks_config['contestant1'], 
        )

    @task
    def contestant2(self) -> Task:
        return Task(
            config=self.tasks_config['contestant2'], 
        )
    
    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Storytellingbattle crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
