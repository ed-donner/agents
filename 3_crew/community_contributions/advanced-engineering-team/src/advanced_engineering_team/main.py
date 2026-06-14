#!/usr/bin/env python
import os
import re
import sys
import argparse
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from .crew import AdvancedEngineeringTeam

DEFAULT_REQUIREMENTS = """
A simple account management system for a trading simulation platform.
The system should allow users to create an account, deposit funds, and withdraw funds.
The system should allow users to record that they have bought or sold shares, providing a quantity.
The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
The system should be able to report the holdings of the user at any point in time.
The system should be able to report the profit or loss of the user at any point in time.
The system should be able to list the transactions that the user has made over time.
The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
 from buying more shares than they can afford, or selling shares that they don't have.
 The system has access to a function get_share_price(symbol) which returns the current price of a share,
 and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
"""

OUTPUT_DIR = "output"


def clean_output_files(module_name: str):
    """Strip markdown from generated .py files, extract code blocks."""
    py_files = [
        os.path.join(OUTPUT_DIR, module_name),
        os.path.join(OUTPUT_DIR, "app.py"),
        os.path.join(OUTPUT_DIR, f"test_{module_name}"),
    ]
    for filepath in py_files:
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as f:
            content = f.read()

        cleaned = _extract_code_from_markdown(content)
        if cleaned and cleaned != content:
            with open(filepath, "w") as f:
                f.write(cleaned)
            print(f"  Cleaned markdown from {filepath}")
        elif not cleaned and content.strip():
            with open(filepath, "w") as f:
                f.write(content)
        elif not content.strip():
            print(f"  Warning: {filepath} is empty")


def _extract_code_from_markdown(text: str) -> str:
    """Extract Python code from LLM output.

    Prefers content inside ```python...``` blocks.
    Falls back to extracting def/class/import lines if no blocks found.
    Strips <think> blocks and leading prose.
    """
    text = re.sub(r"(?s)<think>.*?</think>", "", text)

    lines = text.split("\n")
    in_block = False
    blocks = []
    current = []
    for line in lines:
        if line.strip().startswith("```"):
            if in_block:
                blocks.append("\n".join(current))
                current = []
            in_block = not in_block
            continue
        if in_block:
            current.append(line)

    if blocks:
        return max(blocks, key=len).strip()

    text = re.sub(r"```[a-z]*", "", text)
    lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
    stripped = "\n".join(lines).strip()

    code_lines = []
    seen_def = False
    for line in stripped.split("\n"):
        if re.match(r"^(import |from |def |class |@)", line):
            seen_def = True
        if seen_def:
            code_lines.append(line)

    if code_lines:
        return _find_valid_python(code_lines)

    return stripped


def _find_valid_python(lines: list[str]) -> str:
    """Find the longest valid Python prefix from a list of lines."""
    for i in range(len(lines), 0, -1):
        block = "\n".join(lines[:i])
        try:
            compile(block, "<output>", "exec")
            return block.strip()
        except SyntaxError:
            continue
    return "\n".join(lines).strip()

    return stripped


def parse_args():
    parser = argparse.ArgumentParser(
        description="Advanced Engineering Team — multi-agent software development"
    )
    parser.add_argument(
        "--requirements", "-r",
        type=str, default=None,
        help="Custom requirements. If omitted, uses default trading account system."
    )
    parser.add_argument(
        "--module", "-m",
        type=str, default="accounts.py",
        help="Output module name (default: accounts.py)"
    )
    parser.add_argument(
        "--class-name", "-c",
        type=str, default="Account",
        help="Main class name (default: Account)"
    )
    return parser.parse_args()


def run():
    args = parse_args()

    requirements = args.requirements
    if not requirements and not sys.stdin.isatty():
        requirements = sys.stdin.read().strip()
    if not requirements:
        requirements = DEFAULT_REQUIREMENTS

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    inputs = {
        "requirements": requirements.strip(),
        "module_name": args.module,
        "class_name": args.class_name,
    }

    print(f"\n{'='*60}")
    print(f"  Advanced Engineering Team")
    print(f"  Module: {args.module}  |  Class: {args.class_name}")
    print(f"{'='*60}\n")

    team = AdvancedEngineeringTeam()

    try:
        result = team.crew().kickoff(inputs=inputs)
        clean_output_files(args.module)
        print(f"\n{'='*60}")
        print(f"  Done! Output files in ./{OUTPUT_DIR}/")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"\nError running crew: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
