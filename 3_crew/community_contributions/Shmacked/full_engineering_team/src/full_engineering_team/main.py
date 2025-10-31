#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from full_engineering_team.crew import FullEngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

requirements = """
A simple account management system for a trading simulation platform.
The system should be able to be interacted with through a web interface.
The system should allow users to create an account, and login to their account.
Before anything can be done, the user must be logged in.
The system should allow users to deposit funds, and withdraw funds.
The system should allow users to record that they have bought or sold shares, providing a quantity.
The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
The system should be able to report the holdings of the user at any point in time.
The system should be able to report the profit or loss of the user at any point in time.
The system should be able to list the transactions that the user has made over time.
The system should prevent the user from withdrawing funds that would leave them with a negative balance, or from buying more shares than they can afford, or selling shares that they don't have.
The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
"""

def run():
    """
    Run the crew.
    """
    my_crew = FullEngineeringTeam().crew()
    inputs = {
        'requirements': requirements,
        'engineers': ", ".join([agent.role for agent in my_crew.agents if agent.role != 'manager']),
    }

    try:
        my_crew.kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
