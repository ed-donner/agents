#!/usr/bin/env python
import warnings

from swe_team.crew import SweTeam

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
class_name = "Account"
module_name = "accounts.py"

def run():
    """
    Run the crew.
    """
    inputs = {
        'requirements': requirements,
        'class_name': class_name,
        'module_name': module_name
    }
    
    
    SweTeam().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
    