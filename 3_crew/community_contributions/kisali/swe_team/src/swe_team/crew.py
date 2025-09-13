from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class SweTeam():
    """SweTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    
    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'], 
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'], 
            verbose=True
        )
    
    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'], 
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=400,
            max_retry_limit=3
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'], 
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=400,
            max_retry_limit=3
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'], 
        )

    @task
    def backend_coding_task(self) -> Task:
        return Task(
            config=self.tasks_config['backend_coding_task'], 
        )

    @task
    def frontend_coding_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_coding_task'], 
        )

    @task
    def test_coding_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_coding_task'], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SweTeam crew"""
       
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )
