# src/prism/crew.py
import sys

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from prism.constants import DEFAULT_CURRENCY, TENORS

from .tools.calculation_tools import (
    calculate_dynamic_thresholds,
    calculate_swap_pnl,
    calculate_years_to_maturity,
    check_trading_signal,
)
from .tools.database_tools import get_all_positions, insert_trade_signal
from .tools.market_data_tools import get_latest_market_rate, store_market_rates
from .utils import logger


@CrewBase
class PrismCrew:
    """Prism Swap Trading Crew."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def market_data_agent(self) -> Agent:
        """Create the Market Data Agent for fetching and storing market rates."""
        logger.debug("Initializing Market Data Agent")
        return Agent(
            config=self.agents_config["market_data_agent"],
            tools=[SerperDevTool(), store_market_rates],
            verbose=True,
        )

    @agent
    def position_manager_agent(self) -> Agent:
        """Create the Position Manager Agent for retrieving portfolio positions."""
        logger.debug("Initializing Position Manager Agent")
        return Agent(
            config=self.agents_config["position_manager_agent"],
            tools=[get_all_positions],
            verbose=True,
        )

    @agent
    def risk_calculator_agent(self) -> Agent:
        """Create the Risk Calculator Agent for computing swap PnL."""
        logger.debug("Initializing Risk Calculator Agent")
        return Agent(
            config=self.agents_config["risk_calculator_agent"],
            tools=[
                calculate_swap_pnl,
                calculate_years_to_maturity,
                get_latest_market_rate,
            ],
            verbose=True,
        )

    @agent
    def risk_manager_agent(self) -> Agent:
        """Create the Risk Manager Agent for calculating dynamic risk thresholds."""
        logger.debug("Initializing Risk Manager Agent")
        return Agent(
            config=self.agents_config["risk_manager_agent"],
            tools=[calculate_dynamic_thresholds],
            verbose=True,
        )

    @agent
    def trading_decision_agent(self) -> Agent:
        """Create the Trading Decision Agent for evaluating signals and making trading decisions."""
        logger.debug("Initializing Trading Decision Agent")
        return Agent(
            config=self.agents_config["trading_decision_agent"],
            tools=[check_trading_signal, insert_trade_signal],
            verbose=True,
        )

    @task
    def fetch_market_data_task(self) -> Task:
        """Create the task for fetching and storing current market rates."""
        return Task(
            config=self.tasks_config["fetch_market_data_task"],
        )

    @task
    def load_positions_task(self) -> Task:
        """Create the task for loading portfolio positions from the database."""
        return Task(
            config=self.tasks_config["load_positions_task"],
        )

    @task
    def set_thresholds_task(self) -> Task:
        """Create the task for calculating and setting dynamic risk thresholds."""
        return Task(
            config=self.tasks_config["set_thresholds_task"],
        )

    @task
    def calculate_risk_task(self) -> Task:
        """Create the task for calculating portfolio risk metrics."""
        return Task(
            config=self.tasks_config["calculate_risk_task"],
        )

    @task
    def make_trading_decision_task(self) -> Task:
        """Create the task for evaluating signals and making final trading decisions."""
        return Task(
            config=self.tasks_config["make_trading_decision_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the Prism Swap Trading crew."""
        logger.info("🤖 Assembling PRISM crew with 5 agents")
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def main():
    """Entry point for crewai run command."""
    try:
        logger.info("🚀 Starting PRISM crew execution")
        inputs = {
            "cycle": 1,
            "tenors": ", ".join(TENORS),
            "currency": DEFAULT_CURRENCY,
        }
        result = PrismCrew().crew().kickoff(inputs=inputs)
        logger.info(f"✅ Crew execution completed: {result}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error during crew execution: {e}")
        sys.exit(1)
