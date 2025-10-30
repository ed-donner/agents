from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai_tools import FileWriterTool, FileReadTool

@CrewBase
class FullEngineeringTeam():
    """FullEngineeringTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def architect(self) -> Agent:
        return Agent(
            config=self.agents_config['architect'],
            verbose=True,
            allow_delegation=True,
            memory=True,
            tools=[FileWriterTool(directory="output"), FileReadTool(directory="output")],
        )

    @agent
    def backend_lead_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_lead_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=900,
            max_retry_limit=5,
            memory=True,
            allow_delegation=True,
            tools=[FileWriterTool(directory="output"), FileReadTool(directory="output")],
        )
    
    @agent
    def frontend_lead_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_lead_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=900,
            max_retry_limit=5,
            memory=True,
            allow_delegation=True,
            tools=[FileWriterTool(directory="output"), FileReadTool(directory="output")],
        )
    
    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=900,
            max_retry_limit=5,
            memory=True,
            tools=[FileWriterTool(directory="output"), FileReadTool(directory="output")],
        )
    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=900,
            max_retry_limit=5,
            memory=True,
            tools=[FileWriterTool(), FileReadTool()],
        )
    
    @agent
    def backend_test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=900,
            max_retry_limit=5,
            memory=True,
            tools=[FileWriterTool(directory="output"), FileReadTool(directory="output")],
        )
    
    @agent
    def frontend_test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=900,
            max_retry_limit=5,
            memory=True,
            tools=[FileWriterTool(directory="output"), FileReadTool(directory="output")],
        )

    @task
    def architect_task(self) -> Task:
        return Task(
            config=self.tasks_config['architect_task'],
        )
    
    @task
    def backend_lead_engineer_task(self) -> Task:
        return Task(
            config=self.tasks_config['backend_lead_engineer_task'],
        )
    
    @task
    def frontend_lead_engineer_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_lead_engineer_task'],
        )
    
    @task
    def backend_engineer_task(self) -> Task:
        return Task(
            config=self.tasks_config['backend_engineer_task'],
        )
    
    @task
    def frontend_engineer_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_engineer_task'],
        )
    
    @task
    def backend_test_engineer_task(self) -> Task:
        return Task(
            config=self.tasks_config['backend_test_engineer_task'],
        )
    
    @task
    def frontend_test_engineer_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_test_engineer_task'],
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the FullEngineeringTeam crew"""

        manager = Agent(config=self.agents_config['manager'], allow_delegation=True, memory=True)

        short_term_memory = ShortTermMemory(
            storage=RAGStorage(embedder_config={
                "provider": "openai",
                "config": {
                    "model_name": "text-embedding-3-small"
                }
            }, type="short_term", path="./memory/")
        )

        long_term_memory = LongTermMemory(
            storage=LTMSQLiteStorage(db_path="./memory/long_term_memory_storage.db")
        )
        
        entity_memory = EntityMemory(storage=RAGStorage(embedder_config={
            "provider": "openai",
            "config": {
                "model_name": "text-embedding-3-small"
            }
        }, type="short_term", path="./memory/"))

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            verbose=True,
            memory=True,
            short_term_memory=short_term_memory,
            long_term_memory=long_term_memory,
            entity_memory=entity_memory,
            manager_agent=manager,
        )
