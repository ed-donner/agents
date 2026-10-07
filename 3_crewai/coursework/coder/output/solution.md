I wrote a Python program in the sandbox to calculate the first 1,000,000 terms of the Leibniz series for π:

`1 - 1/3 + 1/5 - 1/7 + ...`

The script uses Python’s `decimal` module for higher precision, sums 1,000,000 terms, multiplies the result by 4, and prints the approximation.

Final result from running the program:

`3.1415916535897932387126433832791903841971703525036`