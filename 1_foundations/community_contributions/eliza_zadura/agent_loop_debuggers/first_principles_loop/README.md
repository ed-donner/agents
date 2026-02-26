# Buggy Kata

A minimal Python repo for practicing writing agent loops. Contains 4 utility functions with intentionally seeded bugs and a pytest test suite to verify fixes. Run the agent loop from the `agent_tool_loop.py` file, or the `agent_tool_loop.ipynb` notebook.

Reset to the initial buggy state anytime with:
`python buggy_kata/reset_kata.py`

## The Challenge

This repo contains 4 utility functions, each with a bug:

| Function | Purpose | Status |
|----------|---------|--------|
| `reverse_string(s)` | Reverse a string | Buggy |
| `is_prime(n)` | Check if a number is prime | Buggy |
| `find_max(items)` | Find the maximum value in a list | Buggy |
| `word_count(text)` | Count words in a text | Buggy |

### Your agent should

1. Run `pytest -v` to see which tests fail
2. Read the failing test output to understand the bug
3. Fix the bug in `src/utils.py`
4. Repeat until all tests pass

## Expected Failures

When you first run the tests, you should see **7 failing tests** from 4 bugs:

| Bug | Failing Tests |
| :---: | :---: |
| `reverse_string` drops last char | `test_reverse_simple`, `test_reverse_single_char`, `test_reverse_palindrome` |
| `is_prime(1)` returns True | `test_edge_cases` |
| `find_max` returns minimum | `test_find_max_positive`, `test_find_max_negative` |
| `word_count` doesn't split on punctuation | `test_count_with_punctuation` |

## Project Structure

```
buggy_kata/
├── src/
│   ├── __init__.py
│   └── utils.py          # Functions with seeded bugs
├── tests/
│   ├── __init__.py
│   └── test_utils.py     # Test suite
├── requirements.txt
└── README.md
```
