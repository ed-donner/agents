#!/usr/bin/env python
import sys
import warnings
from pathlib import Path
from datetime import datetime

from data_science_crew.tools.sandbox_tools import reset_sandbox, run_sandbox_python, write_sandbox_file, list_sandbox_files, SANDBOX_DIR

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

business_requirements = """
Target Objectives for 'data.csv':
1. Analyze raw e-commerce sales dataset 'data.csv' in the sandbox.
2. Data Strategist designs column schemas, KPI definitions, and analytical pipeline requirements in 'sandbox/design.md'.
3. Data Engineer writes and executes 'data_pipeline.py' producing cleaned data ('cleaned_data.csv') and metrics ('summary_stats.csv').
4. Dashboard Engineer builds an interactive Gradio 6 dashboard ('app.py') with top KPI metric cards, Plotly charts (Revenue by Category, Monthly Trend, Region Breakdown), and dynamic data filters, validating with '_validate.py'.
5. QA Reporter audits calculation consistency and drafts a comprehensive executive business report in 'sandbox/executive_summary.md'.
"""


def test_infra():
    """
    Iteration 1 Verification:
    Reset sandbox, initialize uv packages, auto-generate dataset, and verify
    that pandas/plotly can read data.csv inside Docker sandbox.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("--- ITERATION 1: Initializing Sandbox & Auto-generating Dataset ---")
    reset_sandbox()

    files = list_sandbox_files.func()
    print(f"Sandbox files after reset:\n{files}\n")

    test_script = """import pandas as pd
import plotly.express as px

df = pd.read_csv('data.csv')
print("[SUCCESS] Loaded dataset inside Docker container!")
print(f"Total Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print("\\n--- Sample Data Preview ---")
print(df[['order_id', 'order_date', 'customer_segment', 'category', 'unit_price', 'quantity']].head(3))
"""
    write_sandbox_file.func("test_data.py", test_script)

    print("--- Running Verification Script in Docker Container ---")
    output = run_sandbox_python.func("test_data.py")
    print("\n--- Sandbox Execution Output ---")
    print(output)
    print("--------------------------------")


def run():
    """
    Run the complete Data Science Crew (End-to-End Execution).
    Ensures sandbox and data.csv exist, then kicks off DataScienceCrew.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    data_csv = SANDBOX_DIR / "data.csv"
    if not data_csv.exists():
        print("Sandbox dataset not found. Initializing sandbox...")
        reset_sandbox()

    from data_science_crew.crew import DataScienceCrew
    inputs = {
        'business_requirements': business_requirements,
        'dataset_filename': 'data.csv'
    }

    try:
        DataScienceCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """Train the crew for a given number of iterations."""
    inputs = {
        'business_requirements': business_requirements,
        'dataset_filename': 'data.csv'
    }
    try:
        from data_science_crew.crew import DataScienceCrew
        DataScienceCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        from data_science_crew.crew import DataScienceCrew
        DataScienceCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and return results."""
    inputs = {
        'business_requirements': business_requirements,
        'dataset_filename': 'data.csv'
    }
    try:
        from data_science_crew.crew import DataScienceCrew
        DataScienceCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()
