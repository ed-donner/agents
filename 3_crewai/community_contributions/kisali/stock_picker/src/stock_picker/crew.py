from crewai import Agent, Crew, Process, Task, memory
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from typing import List
from crewai_tools import SerperDevTool
from .tools.push_tool import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage

class TrendingCompanies(BaseModel):
    " A company that is in the news and is attracting attention. "
    name: str = Field(description="Company Name")
    ticker: str = Field(description="Stock Ticker Symbol")
    reason: str = Field(description="Reason why this company is trending in the news.")

class TrendingCompaniesList(BaseModel):
    " List of multiple trending companies that are on the news."
    companies: List[TrendingCompanies] = Field(description="List of companies trending in the news.")

class TrendingCompaniesResearch(BaseModel):
    " Detailed research on a company. "
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis.")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")

class TrendingCompaniesResearchList(BaseModel):
    " A list of detailed research on all the companies. "
    research_list: List[TrendingCompaniesResearch] = Field(description="Comprehensive research on all trending companies")

@CrewBase
class StockPicker():
    " Stock Picker Crew"

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_company_finder'], 
            tools=[SerperDevTool()],
            memory=True
        )

    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'], 
            tools=[SerperDevTool()]
        )

    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'],
            tools=[PushNotificationTool()],
            memory=True
        )

    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'], 
            output_pydantic=TrendingCompaniesList,
        )

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'], 
            output_pydantic=TrendingCompaniesResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'],
        )

    @crew
    def crew(self) -> Crew:
        " Creates the Stock Picker Crew"

        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True
        )

        long_term_memory = LongTermMemory(
            storage=LTMSQLiteStorage(
                db_path="./memory/long_term_mem_store.db"
            )
        )

        short_term_memory = ShortTermMemory(
            storage = RAGStorage(
                embedder_config={
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small"
                    }
                },
                type="short_term",
                path="./memory"
            )
        )

        entity_memory = EntityMemory(
            storage=RAGStorage(
                embedder_config={
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small"
                    }
                },
                type="short_term",
                path="./memory"
            )
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            long_term_memory=long_term_memory,
            short_term_memory=short_term_memory,
            entity_memory=entity_memory
        )