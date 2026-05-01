from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from debate_lmstudio.lmstudio_loader import MODEL, API_KEY, SERVER_API_HOST

llm = LLM( model=MODEL,base_url=SERVER_API_HOST,api_key=API_KEY)

@CrewBase
class Debate():
    """Debate crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config['debater'], 
            verbose=True,
            llm=llm
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'], 
            verbose=True,
            llm=llm

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
        """Creates the Debate crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )
