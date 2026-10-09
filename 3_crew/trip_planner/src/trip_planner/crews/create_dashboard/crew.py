from tabnanny import verbose
from pydantic import Field, BaseModel
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from datetime import date
from crewai_tools import SerperDevTool
from openai import OpenAI, max_retries

    
@CrewBase
class CreateDashboard():
    """Create Dashboard to record trip details from the user"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def backend_coder(self) -> Agent:
        return Agent(config = self.agents_config['backend_coder'],verbose=True, allow_code_execution= True, code_execution_mode ="safe", max_execution_time=200, max_retries=3)

    @agent
    def frontend_coder(self) -> Agent:
        return Agent(config = self.agents_config['frontend_coder'], verbose= True,)

    @task
    def backend_code(self) -> Task:
        return Task(config = self.tasks_config['backend_code'],)

    @task
    def frontend_code(self) -> Task:
        return Task(config = self.tasks_config['frontend_code'],)

    @crew
    def crew(self) -> Crew:

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
    