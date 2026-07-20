from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from modular_code_gen.tools.file_saver import SaveFilesTool

from pydantic import BaseModel, Field
from typing import List
import yaml
from pathlib import Path

class ModuleDescriptions(BaseModel):
    """ Number of modules, name of each of the module and associated description """
    num_module: int = Field(description="Number of modules")
    names: List[str] = Field(description="Name of the modules")
    descriptions: List[str] = Field(description="Description of the modules")


class MainAPIFile(BaseModel):
    """ API source code allowing users to interact with modules """
    source_file: str = Field(description=f"Raw python code of the API file using the backend modules")
    test_file: str = Field(description=f"Raw python code testing the API without launching the GUI")


class ModuleSourceAndTestFiles(BaseModel):
    """ Number of modules, name of each of the module source files and associated raw python code """
    num_module: int = Field(description="Number of modules")
    sources_names: List[str] = Field(description="Name of the module source files")
    test_names: List[str] = Field(description="Name of the module test files")
    sources_raw_code: List[str] = Field(description="Raw python code of the module source files")
    tests_raw_code: List[str] = Field(description="Raw python code of the module test files")

''''
class OutputFilePaths(BaseModel):
    """ List of all written output files and their paths """
    file_names: List[str] = Field(description="Name of the output files")
    file_paths: List[str] = Field(description="Paths of all the output files")
'''



@CrewBase
class EngineeringMembers():
    """EngineeringTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=800, 
            max_retry_limit=10
        )
    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=800, 
            max_retry_limit=10,
            verbose=True
        )
    

    

    @agent
    def file_writer(self) -> Agent:
        return Agent(config=self.agents_config['file_writer'],
                     tools=[SaveFilesTool()],  
                     max_retry_limit=10,
                    verbose=True)


    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],
            output_pydantic=ModuleDescriptions
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
            output_pydantic=ModuleSourceAndTestFiles  
        )

    @task
    def writer_task_back(self) -> Task:
        return Task(config=self.tasks_config['writer_task_back'])
    
    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
            output_pydantic=MainAPIFile
        )

    @task
    def writer_task_front(self) -> Task:
        return Task(config=self.tasks_config['writer_task_front'])
    
    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )