from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from swe_team.guardrails import Guardrails

@CrewBase
class SweTeam():
    """SweTeam crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config['manager'],
            allow_delegation=True,
            verbose=True
        )
    
    @agent
    def technical_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['technical_manager'],
            verbose=True,
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
    
    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],
            guardrails=[Guardrails.validate_design_structure],
        )
    
    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=400,
            max_retry_limit=3
        )
    
    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=400,
            max_retry_limit=3
        )


    @crew
    def crew(self) -> Crew:
        """Create crew"""
        return Crew(
            agents=[
                self.technical_manager(),
                self.backend_engineer(),
                self.frontend_engineer(),
                self.test_engineer()
            ],
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=self.manager(),
        )
