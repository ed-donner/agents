from typing import List
from crewai_tools import  FileReadTool
from ...tools.zip_tool import ZipFolderTool
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ZipCrew:
    """Zip Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def zip_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['zip_engineer'], # type: ignore[index]
            verbose=True,
            tools=[ZipFolderTool()]
    )
    @task
    def zip_task(self) -> Task:
        return Task(
            config=self.tasks_config['zip_task'], # type: ignore[index]
    )

    @crew
    def crew(self) -> Crew:
        """Zip Code Crew"""
        
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
