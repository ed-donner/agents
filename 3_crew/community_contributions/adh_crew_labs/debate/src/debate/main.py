#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from debate.crew import Debate

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'motion': 'There needs to be strict laws that regulates LLMs.',
    }

    try:
        result = Debate().crew().kickoff(inputs=inputs)
        print("\n\n=== FINAL DECISION ===\n\n")
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")