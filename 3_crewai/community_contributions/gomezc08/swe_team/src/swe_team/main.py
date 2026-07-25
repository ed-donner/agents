#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from swe_team.crew import SweTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    inputs = {
        'requirements': """
            1. A backend that tracks expenses with 'amount', 'category', and 'date'.
            2. Logic to calculate total spending and spending by category.
            3. A method to 'save' and 'load' data from a local JSON file.
            4. A Gradio UI with tabs: one for 'Add Expense' and one for 'View Analytics'.
        """,
        'module_name': 'budget_manager',
        'class_name': 'BudgetTracker'
    }

    try:
        SweTeam().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred: {e}")