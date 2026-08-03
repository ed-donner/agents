#!/usr/bin/env python
import os
import warnings
from dotenv import load_dotenv

load_dotenv(override=True)

from code_converter.crew import CodeConverter

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs('outputs', exist_ok=True)

PYTHON_CODE = '''
def lcg(seed, a=1664525, c=1013904223, m=2**32):
    value = seed
    while True:
        value = (a * value + c) % m
        yield value

def max_subarray_sum(n, seed, min_val, max_val):
    lcg_gen = lcg(seed)
    random_numbers = [next(lcg_gen) % (max_val - min_val + 1) + min_val for _ in range(n)]
    max_sum = float('-inf')
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += random_numbers[j]
            if current_sum > max_sum:
                max_sum = current_sum
    return max_sum

def total_max_subarray_sum(n, initial_seed, min_val, max_val):
    total_sum = 0
    lcg_gen = lcg(initial_seed)
    for _ in range(10):
        seed = next(lcg_gen)
        total_sum += max_subarray_sum(n, seed, min_val, max_val)
    return total_sum

n = 3000
initial_seed = 42
min_val = -10
max_val = 10

import time
start_time = time.time()
result = total_max_subarray_sum(n, initial_seed, min_val, max_val)
end_time = time.time()

print("Total Maximum Subarray Sum (10 runs):", result)
print("Execution Time: {:.6f} seconds".format(end_time - start_time))
'''


def run():
    """Run the Python-to-Fortran conversion crew."""
    inputs = {
        'python_code': PYTHON_CODE,
    }
    try:
        result = CodeConverter().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
