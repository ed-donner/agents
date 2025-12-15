from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pydantic import BaseModel, Field
from crewai_tools import SerperDevTool

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


class Trendingcompany(BaseModel):
    """A company that is in the news and attracting attention"""
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock tikcer symbol")
    reason: str = Field(description="Reason this company is trending in the news")

class Trendincompanylist(BaseModel):
    """A list of multiple trending companies that are in the news"""
    companies: List[Trendingcompany] = Field(description="List of companies trending in the news")

class TrendingCompanyResearch(BaseModel):
    """A detailed research on a company"""
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")


class TrendingCompanyResearchList(BaseModel):
    """A list of detailed research on all the companies"""
    research_list: List[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")


@CrewBase
class StockpickerCustom():
    """StockpickerCustom crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def emerging_companies_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['emerging_companies_finder'],tools=[SerperDevTool()])

    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'],tools=[SerperDevTool()])

    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'])

    ##defining task


    @task
    def find_emerging_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_emerging_companies'],
                   output_pydantic=Trendincompanylist)


    @task
    def research_emerging_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_emerging_companies'],
            output_pydantic=TrendingCompanyResearchList)


    @task
    def pick_best_companies(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_companies'])

    @crew
    def crew(self) -> Crew:
        """Creates the StockpickerCustom crew"""
         
        manager = Agent(
            config=self.agents_config['research_manager'],
            allow_delegation=True
         )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True
        )
       
       
       
       
       

        
