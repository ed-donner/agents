#!/usr/bin/env python

import os
import warnings

from fitness_agent.crew import FitnessCrew

warnings.filterwarnings("ignore")

# just making sure output folder exists
os.makedirs('output', exist_ok=True)


def load_user_preferences():
    with open("user_preference.txt", "r", encoding="utf-8") as f:
        return f.read()


def run():
    """
    run the fitness crew
    """

    user_preferences = load_user_preferences()

    inputs = {
        "user_preferences": user_preferences
    }

    try:
        result = FitnessCrew().crew().kickoff(inputs=inputs)

        print("\n\n--- FINAL OUTPUT ---\n")
        print(result.raw)

    except Exception as e:
        raise Exception(f"something broke while running the crew: {e}")


if __name__ == "__main__":
    run()