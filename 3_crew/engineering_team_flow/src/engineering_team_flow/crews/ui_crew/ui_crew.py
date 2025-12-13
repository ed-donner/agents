from typing import List
from crewai_tools import SerperDevTool, FileReadTool
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class UiCrew:
    """Ui Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
            tools=[FileReadTool(), SerperDevTool()],
            allow_code_execution=True,
            code_execution_mode="safe",  
            max_execution_time=500, 
            max_retry_limit=3,
    )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'], 
    )

    @crew
    def crew(self) -> Crew:
        """Creates UI Crew"""
        return Crew(
            agents=self.agents,  
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )
