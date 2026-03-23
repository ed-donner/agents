#!/usr/bin/env python
import sys
import warnings
import os

from datetime import datetime

from coder.crew import Coder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs('output', exist_ok=True)

assignment = 'Write a python program to calculate the first 10,000 terms \
    of this series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + ...'


# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'assignment': assignment,
    }

    try:
        result = Coder().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")