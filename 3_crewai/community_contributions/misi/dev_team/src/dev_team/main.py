#!/usr/bin/env python
import os
import warnings

from dev_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

requirements = """
A simple account management system for a trading simulation platform.
The system should allow users to create an account, deposit funds, and withdraw funds.
The system should allow users to record that they have bought or sold shares, providing a quantity.
The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
The system should be able to report the holdings of the user at any point in time.
The system should be able to report the profit or loss of the user at any point in time.
The system should be able to list the transactions that the user has made over time.
The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
 from buying more shares than they can afford, or selling shares that they don't have.
 The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
The system has to persist the account information, including the balance, holdings, and transaction history, so that it can be retrieved and updated across multiple sessions.
The system should have a registration and login system to manage multiple users, ensuring that each user's data is kept separate and secure.
The system has to create different modules for different functionalities, such as account management, transaction processing, and data persistence, to ensure a clean and maintainable codebase.
"""


def run():
    """
    Run the research crew.
    """
    inputs = {"requirements": requirements}

    # Create and run the crew
    EngineeringTeam().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
