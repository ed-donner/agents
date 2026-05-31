#!/usr/bin/env python
import warnings
import os

from market_researcher.crew import MarketResearcher

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """

    inputs = {
        'target_market': 'D2C cloud kitchen companies',
        'competitor_a': 'Swiggy',
        'competitor_b': 'Zomato',
        'competitor_c': 'Uber Eats',
    }

    try:
        MarketResearcher().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()
