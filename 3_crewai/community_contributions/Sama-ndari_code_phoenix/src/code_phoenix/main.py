#!/usr/bin/env python
import sys
import warnings

from code_phoenix.crew import CodePhoenix

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pydantic")

def run():
    """
    Run the crew.
    """
    print("## Starting CodePhoenix Autonomous Repair...")
    print("## Target: broken_script.py\n")
    
    # We pass the filename to the agents so they know what to read
    inputs = {
        'filename': 'broken_script.py'
    }
    
    try:
        CodePhoenix().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()