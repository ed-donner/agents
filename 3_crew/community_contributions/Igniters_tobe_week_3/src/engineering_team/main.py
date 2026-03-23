#!/usr/bin/env python
import os
import warnings

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

requirements = """
Build a Python e-commerce system with user registration and authentication, a product catalog with categories and search, a shopping cart with add, remove, and quantity updates, order checkout with order history and status, and price calculation with tax.
""".strip()


def run():
    os.makedirs("output", exist_ok=True)
    EngineeringTeam().crew().kickoff(inputs={"requirements": requirements})


if __name__ == "__main__":
    run()
