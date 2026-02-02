
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from datetime import datetime
import os
import yaml

from advanced_investment_crew.tools.yfinance_tool import fetch_market_data_tool

@CrewBase
class AdvancedInvestmentCrew():
    """Advanced ETF Portfolio Analysis Crew"""
    
    agents_config_path = 'src/advanced_investment_crew/config/agents.yaml'
    tasks_config_path = 'src/advanced_investment_crew/config/tasks.yaml'

    def __init__(self):
        """Initialize the crew with necessary tools"""
        self.serper_tool = SerperDevTool()

        # Load YAML configs as dicts
        with open(self.agents_config_path, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(self.tasks_config_path, 'r') as f:
            self.tasks_config = yaml.safe_load(f)

        # Ensure reports directory exists
        os.makedirs('reports', exist_ok=True)
    
    @agent
    def market_data_researcher(self) -> Agent:
         # ✅ Tool'u liste olarak ver
        tools = [fetch_market_data_tool] if fetch_market_data_tool else []
        
        return Agent(
            config=self.agents_config['market_data_researcher'],
            tools=tools,
            verbose=True
        )
    
    @agent
    def portfolio_optimizer(self) -> Agent:
        """Portfolio optimization agent"""
        return Agent(
            config=self.agents_config['portfolio_optimizer'],
            tools=[],
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def risk_analyst(self) -> Agent:
        """Risk analysis agent"""
        return Agent(
            config=self.agents_config['risk_analyst'],
            tools=[],
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def report_writer(self) -> Agent:
        """Report writing agent"""
        return Agent(
            config=self.agents_config['report_writer'],
            tools=[],
            verbose=True,
            allow_delegation=False
        )
    
    @task
    def fetch_market_data(self) -> Task:
        """Task to fetch and analyze market data"""
        return Task(
            config=self.tasks_config['fetch_market_data'],
            agent=self.market_data_researcher()
        )
    
    @task
    def optimize_portfolio(self) -> Task:
        """Task to optimize portfolio"""
        return Task(
            config=self.tasks_config['optimize_portfolio'],
            agent=self.portfolio_optimizer()
        )
    
    @task
    def assess_risks(self) -> Task:
        """Task to assess portfolio risks"""
        return Task(
            config=self.tasks_config['assess_risks'],
            agent=self.risk_analyst()
        )
    
    @task
    def generate_investment_report(self) -> Task:
        """Task to generate final investment report"""
        return Task(
            config=self.tasks_config['generate_investment_report'],
            agent=self.report_writer()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Advanced Investment Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
