# src/financial_researcher/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from financial_researcher.tools.financial_tools import StockDataTool, FinancialRatiosTool

@CrewBase
class FinancialAnalysisCrew():
    """Advanced financial analysis crew for comprehensive investment research"""

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['market_analyst'],
            verbose=True,
            tools=[StockDataTool(), SerperDevTool()]
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst'],
            verbose=True,
            tools=[StockDataTool(), FinancialRatiosTool()]
        )

    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_analyst'],
            verbose=True,
            tools=[StockDataTool(), SerperDevTool()]
        )

    @agent
    def forecast_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['forecast_analyst'],
            verbose=True,
            tools=[StockDataTool()]
        )

    @agent
    def investment_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['investment_advisor'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def market_data_task(self) -> Task:
        return Task(config=self.tasks_config['market_data_task'])

    @task
    def financial_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['financial_analysis_task'])

    @task
    def risk_assessment_task(self) -> Task:
        return Task(config=self.tasks_config['risk_assessment_task'])

    @task
    def forecast_task(self) -> Task:
        return Task(config=self.tasks_config['forecast_task'])

    @task
    def investment_recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['investment_recommendation_task'],
            output_file='output/investment_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the financial analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
