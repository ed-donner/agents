#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from housepurchase_debate.crew import HousepurchaseDebate

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'debater1': 'Sarah Johnson',
        'debater2': 'Michael Chen',
        'motion': 'One should always rent a house for whole life instead of buying a house. The cost of renting a house is less than the cost of buying a house.',
    }
    
    try:
        result=HousepurchaseDebate().crew().kickoff(inputs=inputs)
        print(result)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")