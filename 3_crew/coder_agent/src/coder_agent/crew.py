from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class CoderAgent():
    """CoderAgent crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    #One click install for Docker Desktop:
    #https://docs.docker.com/desktop/
    @agent
    def coder(self) -> Agent:
        return Agent(
            config=self.agents_config['coder'], # type: ignore[index]
            verbose=True,
            # Disable code execution so this crew runs without Docker installed.
            # (CrewAI validates Docker whenever `allow_code_execution=True`.)
            allow_code_execution=False,
            max_retry_limit=3 
        )
   
    @task
    def coding_task(self) -> Task:
        return Task(
            config=self.tasks_config['coding_task'],
            
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,  
            process=Process.sequential,
            verbose=True,
        )
