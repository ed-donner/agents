from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List
from .tools.push_tool import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage


class TrendingSchoolTeacher(BaseModel):
    """ A school and teacher that is in the news and attracting attention """
    school_name: str = Field(description="School name")
    teacher_name: str = Field(description="Teacher name")
    reason: str = Field(description="Reason this school and teacher is trending in the news or non-news and their initiatives,achievements, unique approaches, etc.")

class TrendingSchoolTeacherList(BaseModel):
    """ List of multiple trending schools and teachers that are in the news """
    schools_teachers: List[TrendingSchoolTeacher] = Field(description="List of schools and teachers trending in the news")

class TrendingSchoolTeacherResearch(BaseModel):
    """ Detailed research on a school and teacher """
    name: str = Field(description="School and teacher name")
    global_school_position: str = Field(description="Current global school position and competitive analysis")
    global_teacher_position: str = Field(description="Current global teacher position and competitive analysis")


class TrendingSchoolTeacherResearchList(BaseModel):
    """ A list of detailed research on all the schools and teachers """
    research_list: List[TrendingSchoolTeacherResearch] = Field(description="Comprehensive research on all trending schools and teachers")

@CrewBase
class BestSchoolTeacherPicker():
    """BestSchoolTeacherPicker crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def trending_schools_teachers_finder(self) -> Agent:
        return Agent(config=self.agents_config['trending_schools_teachers_finder'],
                     tools=[SerperDevTool()], memory=True)
    
    @agent
    def global_educational_researcher(self) -> Agent:
        return Agent(config=self.agents_config['global_educational_researcher'], 
                     tools=[SerperDevTool()])

    @agent
    def best_school_teacher_picker(self) -> Agent:
        return Agent(config=self.agents_config['best_school_teacher_picker'], 
                     tools=[PushNotificationTool()], memory=True)
    
    @task
    def find_trending_schools_teachers(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_schools_teachers'],
            output_pydantic=TrendingSchoolTeacherList,
        )

    @task
    def research_trending_schools_teachers(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_schools_teachers'],
            output_pydantic=TrendingSchoolTeacherResearchList,
        )

    @task
    def pick_best_school_teacher(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_school_teacher'],
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the BestSchoolTeacherPicker crew"""

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
            memory=True,
            # Long-term memory for persistent storage across sessions
            long_term_memory = LongTermMemory(
                storage=LTMSQLiteStorage(
                    db_path="./memory/long_term_memory_storage.db"
                )
            ),
            # Short-term memory for current context using RAG
            short_term_memory = ShortTermMemory(
                storage = RAGStorage(
                        embedder_config={
                            "provider": "ollama",
                            "config": {
                                "model": 'nomic-embed-text'
                            }
                        },
                        type="short_term",
                        path="./memory/"
                    )
                ),            # Entity memory for tracking key information about entities
            entity_memory = EntityMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "ollama",
                        "config": {
                            "model": 'nomic-embed-text'
                        }
                    },
                    type="short_term",
                    path="./memory/"
                )
            ),
        )
