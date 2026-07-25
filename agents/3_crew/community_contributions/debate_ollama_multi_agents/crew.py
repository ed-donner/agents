from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

llm_debater = LLM( model="ollama/phi4-reasoning:plus",base_url="http://localhost:11434" )
llm_opposer  =  LLM( model="ollama/deepseek-r1:latest",base_url="http://localhost:11434" )
llm_judge  =  LLM( model="ollama/gemma3:27b",base_url="http://localhost:11434" )



@CrewBase
class Debate():
    """Debate crew"""


    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config['debater'],
            llm=llm_debater,
            verbose=True
        )

    @agent
    def opponent(self) -> Agent:
        return Agent(
            config=self.agents_config['opponent'],
            llm=llm_opposer,
            verbose=True
        )
    
    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],
            llm=llm_judge,
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
            config=self.tasks_config['opponent'],
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
