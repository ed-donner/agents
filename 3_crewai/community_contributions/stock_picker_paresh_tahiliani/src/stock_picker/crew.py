import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.memory import Memory
from pydantic import BaseModel, Field
from .tools.search_tool import web_search
from .tools.push_tool import send_push_notification

load_dotenv(override=True)
# CrewAI's native Gemini provider reads GEMINI_API_KEY, so map it from GEMINIAI_API_KEY
os.environ.setdefault("GEMINI_API_KEY", os.getenv("GEMINIAI_API_KEY", ""))


def gemini_memory(**kwargs) -> Memory:
    """ memory=True defaults to OpenAI (gpt-4o-mini + OpenAI embeddings), so configure Gemini instead.
    The "google-vertex" embedder uses the Gemini API (not Vertex) when given an api_key """
    return Memory(
        # a different model from the agents: the free tier quota (15 requests/min) is per model
        llm="gemini/gemini-3.1-flash-lite",
        embedder={"provider": "google-vertex",
                  "config": {"api_key": os.getenv("GEMINI_API_KEY"), "model_name": "gemini-embedding-001"}},
        **kwargs,
    )


class TrendingCompany(BaseModel):
    """ A company that is in the news and attracting attention """
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")

class TrendingCompanyList(BaseModel):
    """ List of multiple trending companies that are in the news """
    companies: list[TrendingCompany] = Field(description="List of companies trending in the news")

class TrendingCompanyResearch(BaseModel):
    """ Detailed research on a company """
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")

class TrendingCompanyResearchList(BaseModel):
    """ A list of detailed research on all the companies """
    research_list: list[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")

@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(config=self.agents_config['trending_company_finder'],
                     tools=[web_search], memory=gemini_memory())
    
    @agent
    def financial_researcher(self) -> Agent:
        return Agent(config=self.agents_config['financial_researcher'],
                     tools=[web_search], memory=gemini_memory())

    @agent
    def stock_picker(self) -> Agent:
        return Agent(config=self.agents_config['stock_picker'], 
                     tools=[send_push_notification], memory=gemini_memory())
    
    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList,
        )

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        manager = Agent(config=self.agents_config['manager'], 
                        memory=gemini_memory())

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            tracing=True,
            manager_agent=manager,
            max_rpm=12, # stay under the Gemini free tier limit of 15 requests/min; the crew waits instead of failing
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
