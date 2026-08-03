#!/usr/bin/env python
import warnings
import os

from igniters_olawale.crew import IgnitersOlawale

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

idea = """
A social media platform for connecting with people who share the same interests and hobbies.
"""


def run():
   
    inputs = {
        'idea': idea,
    }

    result = IgnitersOlawale().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
