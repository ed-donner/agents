#!/usr/bin/env python

from dotenv import load_dotenv

load_dotenv()  # This reads .env into the environment

import os
import sys
import warnings

from datetime import datetime





from financialresearch_serp.crew import FinancialresearchSerp

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        'company': 'Apple',
    }
    
    result = FinancialresearchSerp().crew().kickoff(inputs=inputs)
    print(result.raw)

if __name__ == "__main__":
    run()