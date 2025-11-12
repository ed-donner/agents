from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class TddEngineeringTeam():
    """TddEngineeringTeam crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'], # type: ignore[index]
            max_execution_time=500, 
            max_retry_limit=3,
            verbose=True
        )  
    
    @agent
    def requirement_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['requirement_analyst'], # type: ignore[index]
            max_execution_time=500, 
            max_retry_limit=3,
            verbose=True
        )

    @agent
    def test_case_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_case_designer'], # type: ignore[index]
            max_execution_time=500, 
            max_retry_limit=3,
            verbose=True
        )        

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'], # type: ignore[index]
            max_execution_time=500, 
            max_retry_limit=3,
            verbose=True
        ) 

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'], # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe", 
            max_execution_time=500, 
            max_retry_limit=5,
            verbose=True
        )    

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            allow_code_execution=True,
            code_execution_mode="safe", 
            max_execution_time=500, 
            max_retry_limit=5,
            verbose=True
        )
    
    @agent
    def python_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['python_writer_agent'], # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe", 
            max_execution_time=500, 
            max_retry_limit=5,
            verbose=True
        )              

    @task
    def create_userstories_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_userstories_task'] # type: ignore[index]
        )

    @task
    def analyze_requirements(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_requirements'] # type: ignore[index]
        )        

    @task
    def test_case_designer_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_case_designer_task'] # type: ignore[index]
        ) 
    
    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'] # type: ignore[index]
        )     

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'] # type: ignore[index]
        )

    @task
    def python_write_backend_task(self) -> Task:
        return Task(
            config=self.tasks_config['python_write_backend_task'] # type: ignore[index]
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
        )     

    @task
    def python_write_frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['python_write_frontend_task'] # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""
       
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
