#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from stockpicker.crew import Stockpicker

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """Run the research crew"""
    inputs = {
        'sector': 'Technology',
        'date': str(datetime.now().strftime('%B %Y'))
    }
    result = Stockpicker().crew().kickoff(inputs=inputs)
    print(result.raw)


if __name__ == "__main__":
    run()