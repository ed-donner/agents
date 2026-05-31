#!/usr/bin/env python
import warnings
from marketing_team.crew import MarketingTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """ Run the crew."""
    try:
        MarketingTeam().crew().kickoff()
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
