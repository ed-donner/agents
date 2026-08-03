from multiprocessing import process
from tabnanny import verbose
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pydantic import BaseModel , Field
from crewai_tools import SerperDevTool
from crewai.memory import LongTermMemory,ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.llm_sqlite_storage import LTMSQLiteStorage


##Setting up structured outputs###

class EmergingCompany(BaseModel):
    """ A company that is in the news and attracting attention"""

    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symnol")
    reason: str = Field(description="Reason this company is trending in the news")


class EmergingCompanyList(BaseModel):
    """List of multiple emerging companies that are in the news"""
    companies: List[EmergingCompany] = Field(description="List of companies emerging and trending in the news")


class EmergingCompaniesResearch(BaseModel):
    """Detailed research on a company"""
    name: str = Field(description="Company name")
    market_positon: str = Field(description="Current market position and competitive analysis")
    future_outlook : str = Field(description="Future outlook and growth prospect")
    investment_potential : str = Field(description="Investment potential and suitability for investment")


class EmergingCompaniesResearchList(BaseModel):
    """List of detailed research on the companies"""
    research_List: List[EmergingCompaniesResearch] = Field(description="Comprehensive research on all trending companies")



@CrewBase
class LatestMarketResearch():
    """LatestMarketResearch crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

##Setting up all agents###
    @agent
    def emerging_companies_finder(self)-> Agent:
        return Agent(config=self.agents_config['emerging_companies_finder'], tools=[SerperDevTool()], memory=True)

    @agent
    def financial_researcher(self)-> Agent:
        return Agent(config=self.agents_config['financial_researcher'], tools=[SerperDevTool()])

    @agent
    def stock_picker(self) -> Agent:
        return Agent(config=self.agents_config['stock_picker'], memory=True)





##Setting up all tasks###
    @task
    def find_emerging_companies(self) -> Task:
        return Task(config=self.tasks_config['find_emerging_companies'], output_pydantic=EmergingCompanyList)
    
    @task
    def research_emerging_companies(self) -> Task:
        return Task(config=self.tasks_config['research_emerging_companies'],output_pydantic=EmergingCompaniesResearchList)

    @task
    def best_company_picker(self) -> Task:
        return Task(config=self.tasks_config['pick_best_companies'])



##Setting up the crew###



    @crew
    def crew(self) -> Crew:
        """Creates the stockpicker crew"""

        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True
        )

        short_term_memory = ShortTermMemory(

            storage = RAGStorage(
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
                    "provider":"openai",
                    "config":{
                        "model":'text-embedding-3-small'
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
            manager_agent=manager,
            memory = True,
            short_term_memory = short_term_memory,
            long_term_memory=long_term_memory,
            entity_memory = entity_memory            
            
            
            )
    


