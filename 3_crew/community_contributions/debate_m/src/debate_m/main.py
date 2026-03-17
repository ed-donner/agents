#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from debate_m.crew import DebateM

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'Computer Science practical university curriculum',
        'motion' : 'University curricula should be more practical and focused on real-world skills via internships and practical projects'
    }

    try:
        DebateM().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

