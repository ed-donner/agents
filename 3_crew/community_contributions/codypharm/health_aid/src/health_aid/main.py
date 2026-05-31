#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from health_aid.crew import HealthAid

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

PATIENT_DATA = """
    Name: John Doe
    Age: 52
    Blood Pressure: 145/95
    Glucose: 210 mg/dL
    BMI: 31.2
    Cholesterol: 240 mg/dL
    Current Medications: Metformin 500mg
    Medical History: Type 2 Diabetes, Hypertension
"""

PATIENT_DATA_CLEAR = """
    Name: Jane Smith
    Age: 34
    Blood Pressure: 118/76
    Glucose: 89 mg/dL
    BMI: 22.4
    Cholesterol: 175 mg/dL
    Current Medications: None
    Medical History: None
"""

def run():
    """Run the crew — uses critical patient to test intervention path."""
    inputs = {
        "patient_data": PATIENT_DATA,
        "current_year": str(datetime.now().year)
    }
    try:
        HealthAid().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def run_clear():
    """Run the crew — uses healthy patient to test skip path."""
    inputs = {
        "patient_data": PATIENT_DATA_CLEAR,
        "current_year": str(datetime.now().year)
    }
    try:
        HealthAid().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """Train the crew for a given number of iterations."""
    inputs = {
        "patient_data": PATIENT_DATA,
        "current_year": str(datetime.now().year)
    }
    try:
        HealthAid().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        HealthAid().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and returns the results."""
    inputs = {
        "patient_data": PATIENT_DATA,
        "current_year": str(datetime.now().year)
    }
    try:
        HealthAid().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")