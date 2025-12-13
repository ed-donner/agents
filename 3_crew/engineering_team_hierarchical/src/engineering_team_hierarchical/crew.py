from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool, FileReadTool
from tools.zip_tool import ZipFolderTool

@CrewBase
class EngineeringTeamHierarchical():
    """EngineeringTeamHierarchical crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config='config/agents.yaml'
    tasks_config='config/tasks.yaml'

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'], 
            verbose=True,
            max_reasoning_attempts=3,
            max_iter=3,
            tools=[SerperDevTool()]
    )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'], # type: ignore[index]
            verbose=True,
            # allow_code_execution=True,
            # code_execution_mode="safe",  # Uses Docker for safety
            # max_execution_time=500, 
            # max_retry_limit=3,
            tools=[FileReadTool()]
    )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'], # type: ignore[index]
            verbose=True,
            # max_execution_time=500, 
            # max_retry_limit=3,
            tools=[FileReadTool()]
    )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'], # type: ignore[index]
            verbose=True,
            # allow_code_execution=True,
            # code_execution_mode="safe",  # Uses Docker for safety
            # max_execution_time=500, 
            # max_retry_limit=3,
            tools=[FileReadTool()]
    )

    @agent
    def zip_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['zip_engineer'], # type: ignore[index]
            verbose=True,
            tools=[FileReadTool(), ZipFolderTool()]
    )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'], # type: ignore[index]
            #output_file='report.md'
    )
    
    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'], # type: ignore[index]
            #output_file='report.md'
    )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'], # type: ignore[index]
            #output_file='report.md'
    )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'], # type: ignore[index]
            #output_file='report.md'
    )

    @task
    def zip_task(self) -> Task:
        return Task(
            config=self.tasks_config['zip_task'], # type: ignore[index]
    )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeamCopy crew"""
       
        manager = Agent(
        config=self.agents_config['manager'],
        allow_delegation=True
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            # memory=True,
            # long_term_memory = ShortTermMemory(
            #     storage = RAGStorage(
            #             embedder_config={
            #                 "provider": "openai",
            #                 "config": {
            #                     "model_name": 'text-embedding-3-small'
            #                 }
            #             },
            #             type="short_term",
            #             path="./memory/"
            #         )
            # ), 
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
