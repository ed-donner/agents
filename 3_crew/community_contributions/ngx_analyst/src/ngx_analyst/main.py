#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from ngx_analyst.crew import NgxAnalyst

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'sectors': ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer Goods', 'Construction', 'Retail', 'Telecommunications']
    }

    result = NgxAnalyst().crew().kickoff(inputs=inputs)

    print("\n\n=== FINAL REPORT ===\n\n")
    print(result.raw)

if __name__ == "__main__":
    run()