from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field, config
from typing import List
from .tools.push_tool import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
import os

class SuitableUniversity(BaseModel):
    """ A university that is a good fit for the student """
    name: str = Field(description="University name")
    location: str = Field(description="University location")
    reason: str = Field(description="Reason why this university is a good fit for the student")

class SuitableUniversityList(BaseModel):
    """ A list of universities that are a good fit for the student """
    universities: List[SuitableUniversity] = Field(description="List of universities that are a good fit for the student")

class UniversityResearch(BaseModel):
    """ A detailed research on a university """
    name: str = Field(description="University name")
    location: str = Field(description="University location")
    program: str = Field(description="Program name")
    size: int = Field(description="University size")
    tuition: int = Field(description="University tuition")
    acceptance_rate: float = Field(description="University acceptance rate")
    graduation_rate: float = Field(description="University graduation rate")
    student_to_faculty_ratio: float = Field(description="University student to faculty ratio")
    student_to_staff_ratio: float = Field(description="University student to staff ratio")
    student_to_teacher_ratio: float = Field(description="University student to teacher ratio")
    student_to_teacher_ratio: float = Field(description="University student to teacher ratio")
    reason: str = Field(description="Reason why this university is a good fit for the student")

class UniversityResearchList(BaseModel):
    """ A list of detailed research on universities """
    research_list: List[UniversityResearch] = Field(description="Comprehensive research on all suitable universities")

@CrewBase
class UniversityPicker():
    """UniversityPicker crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def suitable_university_finder(self) -> Agent:
        return Agent(config=self.agents_config['suitable_university_finder'], verbose=True, tools = [SerperDevTool()])

    @agent
    def university_researcher(self) -> Agent:
        return Agent(config=self.agents_config['university_researcher'], verbose=True, tools = [SerperDevTool()])
    
    @agent
    def university_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['university_picker'], 
            verbose=True, 
            tools = [PushNotificationTool()], 
            memory=True,
        )

    @task
    def find_suitable_universities_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_suitable_universities_task'], 
            output_pydantic=SuitableUniversityList
        )
    
    @task
    def research_universities_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_universities_task'], 
            output_pydantic=UniversityResearchList
        )
    
    @task
    def pick_best_university_task(self) -> Task:
        return Task(config=self.tasks_config['pick_best_university_task'])


    @crew
    def crew(self) -> Crew:
        """Creates the UniversityPicker crew"""
        manager = Agent(
            config=self.agents_config['manager'], 
            allow_delegation=True
        )

        # define memory.
        short_term_memory = ShortTermMemory(
            storage=RAGStorage(
                embedder_config={
                    "provider": "openai",
                    "config": {
                        "model": 'text-embedding-3-small'
                    }
                },
                type="short_term",
                path="./memory/"
            )
        )
        long_term_memory = LongTermMemory(
            storage=LTMSQLiteStorage(
                db_path="./memory/long_term_memory_storage.db"
            )
        )
        entity_memory = EntityMemory(
            storage=RAGStorage(
                embedder_config={
                    "provider": "openai",
                    "config": {
                        "model": 'text-embedding-3-small'
                    }
                },
                type="short_term",
                path="./memory/"
            )
        )

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.hierarchical,
            verbose=True,
            manager_agent = manager,
            short_term_memory = short_term_memory,
            long_term_memory = long_term_memory,
            entity_memory = entity_memory
        )
