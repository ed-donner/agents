from typing import List
from crewai_tools import SerperDevTool, FileReadTool
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class CodeCrew:
    """Code Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    
    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'], # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3,
            tools=[FileReadTool(), SerperDevTool()]
    )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'], # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=2,
            memory=True,
            tools=[FileReadTool(), SerperDevTool()]
    )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'], # type: ignore[index]
            #output_file='report.md'
    )
    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'], # type: ignore[index]
            #output_file='report.md'
    )

    @crew
    def crew(self) -> Crew:
        """Creates Code Crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
