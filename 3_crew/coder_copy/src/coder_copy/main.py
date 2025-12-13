#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from coder_copy.crew import CoderCopy

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
from dotenv import load_dotenv
load_dotenv()
from dotenv import load_dotenv
import os
load_dotenv(override=True)  # ensure .env keys override system vars
print("DEBUG OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

os.makedirs('output', exist_ok=True)


def run():
    """
    Run the crew.
    """
    assignment= "Write python script that webscrapes pmi.com webpage, after it remembers webpage text and based on that information determines language of the web page after it checks html lang attribute and compares it if it is as checked in first step"
    inputs = {
        'assignment': assignment 
    }

    try:
      result =  CoderCopy().crew().kickoff(inputs=inputs)
      print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        CoderCopy().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        CoderCopy().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        CoderCopy().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = CoderCopy().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
