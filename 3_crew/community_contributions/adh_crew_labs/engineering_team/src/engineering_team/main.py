#!/usr/bin/env python
import sys
import warnings
import os

from datetime import datetime

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

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
"""

module_name = "accounts.py"
class_name = "Account"

def run():
    """
    Run the crew.
    """
    # with open(f"output/user_stories.md", "r", encoding="utf-8") as f:
    #     user_stories = f.read()

    # with open(f"output/accounts.py_design.md", "r", encoding="utf-8") as f:
    #     design = f.read()
    inputs = {
        'requirements': requirements,
        'output_file': 'output/user_stories.md',
        'module_name': module_name,
        'class_name': class_name,
        # 'user_stories': user_stories,
        # 'design': design
    }

    try:
        EngineeringTeam().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
