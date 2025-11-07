#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from qa_testing_team.crew import QaTestingTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    with open(f"output/stories/user_stories.md", "r", encoding="utf-8") as f:
        user_stories = f.read()    

    inputs = {
        'user_stories': user_stories,
        'application_url': 'http://127.0.0.1:7860'
    }

    try:
        QaTestingTeam().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
