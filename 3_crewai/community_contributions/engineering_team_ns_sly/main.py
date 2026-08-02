#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements = """
A simple Library management system for a school.
Develop a complete Library System. You must implement 3 distinct modules: 
1. models.py (Data structures for Books and Members), 
2. logic.py (Borrowing and Return business logic), 
3. storage.py (JSON persistence layer).
Each module must start with a comment '# filename: <name>.py.
"""
module_name = "library_system"
class_name = "LibraryManager"


def run():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # Create and run the crew
    result = EngineeringTeam().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()