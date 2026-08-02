import sys
import warnings
import os
from datetime import datetime
from moodnurish.crew import AffectAI


def run():
    print("🧠🍽️ AffectAI - Mood to Food Intelligence\n")

    user_input = input("How are you feeling today?\n> ")

    crew = AffectAI().crew()

    result = crew.kickoff(inputs={
        "user_input": user_input
    })

    print("\n✨ Final Response:\n")
    print(result)


if __name__ == "__main__":
    run()