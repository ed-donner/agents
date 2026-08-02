#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from .crew import NewsCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
import os
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'Iran and USA war',
    }

    try:
        result=NewsCrew().crew().kickoff(inputs=inputs)
        print(result)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


if __name__ == "__main__":
    run()