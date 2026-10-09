#!/usr/bin/env python
import sys
import warnings
import os

from datetime import datetime

from realmadridnextbestfit.crew import Realmadridnextbestfit

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        'region' : 'Europe',
        'current_year' : '2026'
    }
    
    result = Realmadridnextbestfit().crew().kickoff(inputs=inputs)

    
    print(result.raw)

if __name__ == '__main__':
    run()