#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from stockpicker_custom.crew import StockpickerCustom

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")



def run():
    """
    Run the Research Crew.
    """
    inputs = {
        'sector': 'technology',
        'region': 'Africa'
    }
    result = StockpickerCustom().crew().kickoff(inputs=inputs)

    print("\n\n=== FINAL DECISION ===\n\n")
    print(result.raw)

if __name__ == "__main__":
    run()




















inputs=inputs)




















nputs=inputs)

