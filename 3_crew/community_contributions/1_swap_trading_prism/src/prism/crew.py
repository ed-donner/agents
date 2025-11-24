# src/prism/crew.py
import sys

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from .database import initialize_database
from .tools import (
    calculate_dynamic_thresholds,
    calculate_swap_pnl,
    calculate_years_to_maturity,
    check_trading_signal,
    get_all_positions,
    get_latest_market_rate,
    insert_trade_signal,
    store_market_rates,
)

# Trading configuration constants
TENORS = ["2Y", "5Y", "10Y", "30Y"]
DEFAULT_CURRENCY = "USD"


@CrewBase
class PrismCrew:
    """Prism Swap Trading Crew."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def market_data_agent(self) -> Agent:
        """Create the Market Data Agent for fetching and storing market rates."""
        return Agent(
            config=self.agents_config["market_data_agent"],
            tools=[SerperDevTool(), store_market_rates],
            verbose=True,
        )

    @agent
    def position_manager_agent(self) -> Agent:
        """Create the Position Manager Agent for retrieving portfolio positions."""
        return Agent(
            config=self.agents_config["position_manager_agent"],
            tools=[get_all_positions],
            verbose=True,
        )

    @agent
    def risk_calculator_agent(self) -> Agent:
        """Create the Risk Calculator Agent for computing swap PnL."""
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
        return Agent(
            config=self.agents_config["risk_manager_agent"],
            tools=[calculate_dynamic_thresholds],
            verbose=True,
        )

    @agent
    def trading_decision_agent(self) -> Agent:
        """Create the Trading Decision Agent for evaluating signals and making trading decisions."""
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
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def main():
    """Entry point for crewai run command."""
    try:
        # Initialize database before running crew
        initialize_database()

        inputs = {
            "cycle": 1,
            "tenors": ", ".join(TENORS),
            "currency": DEFAULT_CURRENCY,
        }
        PrismCrew().crew().kickoff(inputs=inputs)
        sys.exit(0)
    except Exception:
        sys.exit(1)
