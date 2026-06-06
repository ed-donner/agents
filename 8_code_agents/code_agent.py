"""
Core code agent: write → test → fix loop.
The agent receives a problem description + failing tests.
It writes a solution, runs pytest, reads failures, fixes, and repeats
until tests pass or the iteration / cost budget is exhausted.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

from sandbox import run_pytest

load_dotenv(override=True)

client = OpenAI()

SYSTEM_PROMPT = """You are an expert Python engineer.
Your job is to write correct, clean Python code that passes the given tests.

Rules:
- Only output raw Python code — no markdown fences, no explanation.
- Do not import anything that isn't in the Python standard library unless told otherwise.
- If tests fail, read the error carefully and fix only what's broken.
- Keep functions small and well-named.
"""

FIX_PROMPT = """The tests FAILED. Here is the pytest output:

{pytest_output}

Here is your current solution:

```python
{current_solution}
```

Fix the solution so all tests pass. Output only the corrected Python code."""


@dataclass
class AgentRun:
    problem: str
    tests: str
    solution: str = ""
    iterations: int = 0
    passed: bool = False
    history: list[dict] = field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def log(self, role: str, content: str):
        self.history.append({"role": role, "content": content})


# Approximate cost: GPT-4o-mini input $0.15/1M, output $0.60/1M
COST_PER_INPUT_TOKEN = 0.15 / 1_000_000
COST_PER_OUTPUT_TOKEN = 0.60 / 1_000_000


def _chat(messages: list[dict], model: str = "gpt-4o-mini") -> tuple[str, int, int]:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    content = response.choices[0].message.content or ""
    in_tok = response.usage.prompt_tokens
    out_tok = response.usage.completion_tokens
    return content, in_tok, out_tok


def run_code_agent(
    problem: str,
    tests: str,
    max_iterations: int = 8,
    max_cost_usd: float = 0.50,
    model: str = "gpt-4o-mini",
    verbose: bool = True,
) -> AgentRun:
    """
    Run the write→test→fix loop.

    Args:
        problem:        Natural language description of what to implement.
        tests:          pytest test code (without the import — added automatically).
        max_iterations: Hard cap on LLM calls.
        max_cost_usd:   Stop if estimated spend exceeds this.
        model:          OpenAI model to use.
        verbose:        Print progress.

    Returns:
        AgentRun with final solution, pass/fail, and cost breakdown.
    """
    run = AgentRun(problem=problem, tests=tests)

    # --- Step 1: initial solution ---
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Problem:\n{problem}\n\nTests:\n{tests}\n\nWrite the solution:"},
    ]
    solution, in_tok, out_tok = _chat(messages, model)
    run.solution = solution
    run.total_tokens += in_tok + out_tok
    run.total_cost_usd += in_tok * COST_PER_INPUT_TOKEN + out_tok * COST_PER_OUTPUT_TOKEN
    run.log("assistant", solution)
    run.iterations = 1

    if verbose:
        print(f"[iter 1] Generated initial solution ({len(solution)} chars)")

    # --- Step 2: test → fix loop ---
    for iteration in range(2, max_iterations + 1):
        result = run_pytest(tests, run.solution)

        if verbose:
            print(f"[iter {run.iterations}] pytest → {'PASS' if result.success else 'FAIL'}")
            if not result.success:
                print(result.stdout[-800:])

        if result.success:
            run.passed = True
            break

        if run.total_cost_usd >= max_cost_usd:
            if verbose:
                print(f"[budget] Cost ${run.total_cost_usd:.4f} hit limit ${max_cost_usd}")
            break

        fix_prompt = FIX_PROMPT.format(
            pytest_output=result.stdout[-1500:] + result.stderr[-500:],
            current_solution=run.solution,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": fix_prompt},
        ]
        solution, in_tok, out_tok = _chat(messages, model)
        run.solution = solution
        run.total_tokens += in_tok + out_tok
        run.total_cost_usd += in_tok * COST_PER_INPUT_TOKEN + out_tok * COST_PER_OUTPUT_TOKEN
        run.log("assistant", solution)
        run.iterations = iteration

    else:
        # ran out of iterations — check one final time
        result = run_pytest(tests, run.solution)
        run.passed = result.success

    if verbose:
        status = "PASSED" if run.passed else "FAILED"
        print(f"\n{'='*50}")
        print(f"Result: {status} in {run.iterations} iteration(s)")
        print(f"Cost:   ${run.total_cost_usd:.4f}  ({run.total_tokens} tokens)")
        print(f"{'='*50}")

    return run


if __name__ == "__main__":
    PROBLEM = """
    Write a function `fizzbuzz(n: int) -> list[str]` that returns a list of strings
    for numbers 1 through n:
    - 'FizzBuzz' if divisible by both 3 and 5
    - 'Fizz' if divisible by 3 only
    - 'Buzz' if divisible by 5 only
    - The number as a string otherwise
    """

    TESTS = """
def test_basic():
    result = fizzbuzz(15)
    assert result[0] == '1'
    assert result[2] == 'Fizz'
    assert result[4] == 'Buzz'
    assert result[14] == 'FizzBuzz'

def test_length():
    assert len(fizzbuzz(10)) == 10

def test_no_fizzbuzz_below_15():
    result = fizzbuzz(14)
    assert 'FizzBuzz' not in result
"""

    run = run_code_agent(PROBLEM, TESTS, verbose=True)
    print("\nFinal solution:")
    print(run.solution)
