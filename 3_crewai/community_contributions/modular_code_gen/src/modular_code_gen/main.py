#!/usr/bin/env python
from pathlib import Path
import warnings
import os
from datetime import datetime
import json


from modular_code_gen.crew import EngineeringMembers

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

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
main_file_path = "accounts.py"
API_tool = "gradio"
project_directory = "account_directory"


def run():
    """
    Run the research crew.
    """
    # Ensure output directory exists
    output_dir = Path("explicit_output")
    output_dir.mkdir(exist_ok=True)

    inputs = {
        'requirements': requirements,
        'main_file_path': main_file_path,
        'API_tool': API_tool,
        'project_directory' : project_directory
    }

    # Create and run the crew
    result = EngineeringMembers().crew().kickoff(inputs=inputs)


    # Explore available attributes
    print("Crew raw output type:", type(result.raw))
    print("Tasks:", len(result.tasks_output))

if __name__ == "__main__":
    run()