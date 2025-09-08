#!/usr/bin/env python
import sys
import warnings
import os
import random
from datetime import datetime

from monopolygame.crew import MonopolyCoder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

assignment = 'Write a console based python program to play online game called Monopoly.Program should allow minium 2 players and maximum 4 Players. First Person to get 6 on the dice should play first and followed by other in same order. Monopoly can have famous Soccer Arena & Teams in USA as properties. Person who has maximum Properties or Money by the end of the initial 10 rounds would win the game.'

def run():
    """
    Run the crew.
    """
    inputs = {
        'assignment': assignment,
    }
    
    result = MonopolyCoder().crew().kickoff(inputs=inputs)
    print(result.raw)




