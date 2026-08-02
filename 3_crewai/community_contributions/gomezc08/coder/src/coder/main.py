#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from coder.crew import Coder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    assignment = """
    Given a square n x n matrix of integers matrix, rotate it by 90 degrees clockwise.
    You must rotate the matrix in-place. Do not allocate another 2D matrix and do the rotation.

    Example 1:
    Input: matrix = [[1,2,3],[4,5,6],[7,8,9]]
    Output: [[7,4,1],[8,5,2],[9,6,3]]

    Example 2:
    Input: matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]
    Output: [[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]
    """
    inputs = {
        'assignment': assignment,
    }

    try:
        result = Coder().crew().kickoff(inputs=inputs)
        print(f"Result: {result.raw}")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")