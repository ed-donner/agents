from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from crewai_tools import SerperDevTool
from .tools.push_tool import send_push_notification


class TrendingCompany(BaseModel):
    """ A company that is in the news and attracting attention """
    name: str = Field(description="The name of the company")
    description: str = Field(description="The description of the company")
    image_url: str = Field(description="The image URL of the company")
    ticker: str = Field(description="The stock ticker symbol of the company")
    reason: str = Field(description="The reason why the company is trending in the news")

class TrendingCompanyList(BaseModel):
    """ A list of trending companies that are in the news and attracting attention """
    companies: list[TrendingCompany] = Field(description="The list of trending companies in the news")

class TrendingCompanyResearch(BaseModel):
    """ Details research on a company """
    name: str = Field(description="The name of the company")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth potential")
    investment_potential: str = Field(description="Investment potential and sustability for investment")
    board_members: list[str] = Field(description="The board members of the company")
    price: float = Field(description="The current stockprice of the company")
    market_cap: float = Field(description="The market cap of the company")
    halal_investment: bool = Field(description="Whether the company is halal for investment")


class TrendingCompanyResearchList(BaseModel):
    """ A list of details research on a company """
    companies: list[TrendingCompanyResearch] = Field(description="The list of details research on a company")

@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_company_finder'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()], memory=True
        )
# , memory=True
    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()], memory=True
        )

    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'], # type: ignore[index]
            verbose=True,
            tools=[send_push_notification], memory=True
        )

    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'], # type: ignore[index]
            output_pydantic=TrendingCompanyList,
        )

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'], # type: ignore[index]
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'], # type: ignore[index]
            output_file='report.md'
        )      

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        manager =Agent(
            config=self.agents_config['manager'],
            allow_delegation= True,
        )
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            verbose=True,
            tracing=True,
            memory=True,
            manager_agent=manager,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
