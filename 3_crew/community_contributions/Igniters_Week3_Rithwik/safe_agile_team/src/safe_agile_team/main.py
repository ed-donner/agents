#!/usr/bin/env python

import os
import warnings
from safe_agile_team.crew import SafeAgileTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs('output', exist_ok=True)


# the business analyst will turn this into proper requirements for the engineering team
# feature_description = """
# I want a trading simulator where someone can create an account,
# add money, and buy and sell shares. It should track what they own,
# how much money they have, and whether they are making a profit or loss.
# It should stop them doing anything silly like spending money they don't have
# or selling shares they don't own.
# """

feature_description = """

I want a trading simulator where someone can create an account,
add money, and buy and sell shares. It should track what they own,
how much money they have, and whether they are making a profit or loss.
It should stop them doing anything silly like spending money they don't have
or selling shares they don't own.

"""

def run():
    SafeAgileTeam().crew().kickoff(inputs={
        'feature_description': feature_description,
    })


if __name__ == "__main__":
    run()