#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from financial_researcher_test.crew import FinancialResearcherTest

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")



def run():
    """
    Run the financial Reasearcher crew.
    """
    inputs = {
        'company': 'Deustche Bank'
    }

    try:
        result = FinancialResearcherTest().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


