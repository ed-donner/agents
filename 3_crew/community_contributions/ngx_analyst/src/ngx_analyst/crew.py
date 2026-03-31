from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from ngx_analyst.tools.push_tool import PushNotificationTool
from pydantic import BaseModel, Field
from typing import List, Literal



class Company(BaseModel):
    """A company on the NGX(Nigerian Stock Exchange)"""
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    sector: str = Field(description="Sector of the company")
    description: str = Field(description="Description of the company")
    market_cap: float = Field(description="Market cap of the company")
    action: Literal['buy', 'sell', 'hold'] = Field(description="Action to take on the company")
    reason: str = Field(description="Reason for the action")

class CompanyList(BaseModel):
    """A list of companies on the NGX(Nigerian Stock Exchange)"""
    companies: List[Company] = Field(description="List of companies on the NGX(Nigerian Stock Exchange)")

class CompanyReport(BaseModel):
    """A report on a company on the NGX(Nigerian Stock Exchange)"""
    company: Company = Field(description="Company on the NGX(Nigerian Stock Exchange)")
    report: str = Field(description="Report on the company")

class CompanyReportList(BaseModel):
    """A list of reports on companies on the NGX(Nigerian Stock Exchange)"""
    reports: List[CompanyReport] = Field(description="List of reports on companies on the NGX(Nigerian Stock Exchange)")

@CrewBase
class NgxAnalyst():
    """NgxAnalyst crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def senior_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_analyst'],    
            tools=[PushNotificationTool()],
            verbose=True
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst'], 
            tools=[SerperDevTool()],
            verbose=True
        )

    @task
    def select_best_companies(self) -> Task:
        return Task(
            config=self.tasks_config['select_best_companies'], 
            output_file='output/best_companies.json',
            output_pydantic=CompanyList,
        )

    @task
    def create_report(self) -> Task:
        return Task(
            config=self.tasks_config['create_report'], 
            output_file='output/report.md',
            output_pydantic=CompanyReportList,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the NgxAnalyst crew"""

        manager = Agent(config=self.agents_config['manager'], allow_delegation=True, verbose=True)

        return Crew(agents=self.agents, tasks=self.tasks, process=Process.hierarchical, verbose=True, manager_agent=manager)
