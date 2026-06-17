#!/usr/bin/env python
import sys
import warnings
import os
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parents[2]
crewai_home = project_root / ".crewai_home"
crewai_home.mkdir(parents=True, exist_ok=True)
# Ensure CrewAI's appdirs-based storage lands in-project (not ~/Library/...),
# which avoids permission issues in sandboxed/restricted environments.
os.environ["HOME"] = str(crewai_home)

from coder.crew import Coder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

assignment = 'Write a python program to calculate the first 10,000 terms \
    of this series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + ...'

def run():
    """
    Run the crew.
    """
    inputs={
        'assignment': assignment
    }
    
    result = Coder().crew().kickoff(inputs=inputs)
    print(result.raw)




