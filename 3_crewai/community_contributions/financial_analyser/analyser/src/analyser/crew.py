from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from analyser.mock_api import get_mock_stock_data, get_mock_news_sentiment
from typing import List
import yaml
import os

@CrewBase
class Analyser():
    """Market Analysis Crew using DAP Protocol"""

    ##agents: List[BaseAgent]
    ##tasks: List[Task]
    agents_config_path = os.path.join(os.path.dirname(__file__), 'config', 'agents.yaml')
    tasks_config_path = os.path.join(os.path.dirname(__file__), 'config', 'tasks.yaml')

    def __init__(self):
        with open(self.agents_config_path, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(self.tasks_config_path, 'r') as f:
            self.tasks_config = yaml.safe_load(f)

    
    @agent
    def chart_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['chart_analyst'],
            verbose=True
        )

    @agent
    def news_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['news_analyst'], 
            verbose=True
        )

    @agent
    def dap_mediator(self) -> Agent:
        return Agent(
            config=self.agents_config['dap_mediator'], 
            verbose=True
        )

    @task
    def chart_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['chart_analysis_task'],
        )

    @task
    def news_sentiment_task(self) -> Task:
        return Task(
            config=self.tasks_config['news_sentiment_task'], 
            output_file='report.md'
        )

    @task
    def dap_consensus_task(self) -> Task:
        return Task(
            config=self.tasks_config['dap_consensus_task'], 
            output_file='report.md'
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Analyser crew"""


        stock_symbol = "AAPL"
        topic = "Apple stock"


        # Fetch mock data
        stock_data = get_mock_stock_data(stock_symbol)
        news_data = get_mock_news_sentiment(topic)

    # Inject mock data into crew context
        context = {
            "stock_symbol": stock_symbol,
            "news_topic": topic,
            "mock_stock_data": stock_data,
            "mock_news_data": news_data,
        }


        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            context=context,
            verbose=True,
        )
