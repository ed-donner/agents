from typing import List
from crewai_tools import  FileReadTool
from ...tools.zip_tool import ZipFolderTool
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class E2ECrew:
    """E2E Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'], # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=1000, 
            max_retry_limit=2,
            tools=[FileReadTool(), ZipFolderTool()]
    )
    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'], # type: ignore[index]
    )

    @crew
    def crew(self) -> Crew:
        """E2e Tests Code Crew"""
        
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
