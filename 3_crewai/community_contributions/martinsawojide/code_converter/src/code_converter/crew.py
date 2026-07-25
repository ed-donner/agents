import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from code_converter.tools.custom_tool import (
    FortranCompilerTool,
    CodeExecutorTool,
    PythonExecutorTool,
    OutputFormatterTool,
)


@CrewBase
class CodeConverter():
    """Python-to-Fortran Code Converter crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def generator_alpha(self) -> Agent:
        return Agent(
            config=self.agents_config['generator_alpha'],  
            verbose=True,
            max_iter=1,
            allow_delegation=False,
        )

    @agent
    def generator_beta(self) -> Agent:
        return Agent(
            config=self.agents_config['generator_beta'],  
            verbose=True,
            max_iter=1,
            allow_delegation=False,
        )

    @agent
    def generator_gamma(self) -> Agent:
        return Agent(
            config=self.agents_config['generator_gamma'],  
            verbose=True,
            max_iter=1,
            allow_delegation=False,
        )

    @agent
    def optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config['optimizer'],  
            verbose=True,
            max_iter=1,
            allow_delegation=False,
        )

    @agent
    def housekeeper(self) -> Agent:
        return Agent(
            config=self.agents_config['housekeeper'],  
            verbose=True,
            max_iter=1,
            allow_delegation=False,
        )

    @agent
    def code_runner(self) -> Agent:
        return Agent(
            config=self.agents_config['code_runner'],  
            tools=[
                FortranCompilerTool(),
                CodeExecutorTool(),
                PythonExecutorTool(),
                OutputFormatterTool(),
            ],
            verbose=True,
            max_iter=5,
            allow_delegation=False,
        )


    @task
    def generation_alpha_task(self) -> Task:
        return Task(
            config=self.tasks_config['generation_alpha_task'],  
        )

    @task
    def generation_beta_task(self) -> Task:
        return Task(
            config=self.tasks_config['generation_beta_task'],  
        )

    @task
    def generation_gamma_task(self) -> Task:
        return Task(
            config=self.tasks_config['generation_gamma_task'], 
        )

    @task
    def optimization_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimization_task'],  
        )

    @task
    def housekeeping_task(self) -> Task:
        return Task(
            config=self.tasks_config['housekeeping_task'],  
        )

    @task
    def execution_task(self) -> Task:
        return Task(
            config=self.tasks_config['execution_task'],  
        )


    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
