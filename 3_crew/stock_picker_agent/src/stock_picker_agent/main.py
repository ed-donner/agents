#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from stock_picker_agent.crew import StockPickerAgent

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'sector': 'Legal',
        # Some agent templates reference {company}; this crew mostly operates on
        # a discovered list of companies, so we provide a safe default.
        'company': 'Unknown',
    }

    result = StockPickerAgent().crew().kickoff(inputs=inputs)
    print("\n\n=== FINAL DECISION ===\n\n")
    print(result.raw)

if __name__ == "__main__":
    run()
