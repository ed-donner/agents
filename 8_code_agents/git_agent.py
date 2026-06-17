"""
Git-integrated code agent.
Reads a repo file with a failing test, branches, fixes the bug, commits.
Requires: pip install gitpython
"""

import os
import ast
import textwrap
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("gitpython not installed — Git features disabled. Run: pip install gitpython")

client = OpenAI()


def read_ast_summary(source: str) -> str:
    """Return a compact summary of top-level functions/classes in source."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"SyntaxError: {e}"

    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            lines.append(f"  def {node.name}({', '.join(args)}) — line {node.lineno}")
        elif isinstance(node, ast.ClassDef):
            lines.append(f"  class {node.name} — line {node.lineno}")
    return "\n".join(lines) if lines else "  (no top-level definitions found)"


def fix_file_in_repo(
    repo_path: str,
    source_file: str,
    test_file: str,
    branch_name: str = "agent/autofix",
    model: str = "gpt-4o-mini",
) -> dict:
    """
    1. Open the repo at repo_path.
    2. Read source_file and test_file.
    3. Summarize the AST of source_file.
    4. Ask the LLM to fix the source.
    5. Write the fix, run tests (via sandbox), commit on a new branch.

    Returns a dict with keys: branch, commit_hash, passed, solution.
    """
    if not GIT_AVAILABLE:
        return {"error": "gitpython not installed"}

    repo = git.Repo(repo_path)
    src_path = Path(repo_path) / source_file
    test_path = Path(repo_path) / test_file

    original_source = src_path.read_text()
    test_source = test_path.read_text()
    ast_summary = read_ast_summary(original_source)

    print(f"AST summary of {source_file}:\n{ast_summary}\n")

    prompt = f"""You are fixing a bug in a Python file.

File: {source_file}
AST structure:
{ast_summary}

Current source:
```python
{original_source}
```

Tests that must pass (from {test_file}):
```python
{test_source}
```

Output ONLY the corrected Python source for {source_file}. No fences, no explanation."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert Python engineer. Output only raw Python code."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    fixed_source = response.choices[0].message.content or ""

    # Validate syntax before writing
    try:
        ast.parse(fixed_source)
    except SyntaxError as e:
        return {"error": f"LLM returned invalid Python: {e}", "solution": fixed_source}

    # Write fix and run tests
    src_path.write_text(fixed_source)

    from sandbox import run_pytest
    result = run_pytest(test_source, fixed_source)
    passed = result.success

    if not passed:
        # Restore original on failure
        src_path.write_text(original_source)
        return {"passed": False, "pytest_output": result.stdout, "solution": fixed_source}

    # Commit on new branch
    new_branch = repo.create_head(branch_name, force=True)
    new_branch.checkout()
    repo.index.add([source_file])
    commit = repo.index.commit(f"agent/autofix: fix {source_file}\n\nAutomatically fixed by code agent.")

    return {
        "passed": True,
        "branch": branch_name,
        "commit_hash": commit.hexsha[:8],
        "solution": fixed_source,
    }


def demo_without_git():
    """Show AST analysis without needing a real repo."""
    sample = textwrap.dedent("""
    def add(a, b):
        return a - b  # bug: should be +

    def multiply(x, y):
        return x * y

    class Calculator:
        def divide(self, a, b):
            return a / b
    """)
    print("AST Summary of sample code:")
    print(read_ast_summary(sample))

    print("\nAsking LLM to fix the bug...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Fix the bug. Output only corrected Python."},
            {"role": "user", "content": f"Fix the `add` function:\n```python\n{sample}\n```\nTest: assert add(2, 3) == 5"},
        ],
        temperature=0.1,
    )
    fixed = response.choices[0].message.content
    print("Fixed code:")
    print(fixed)
    print("\nAST of fixed code:")
    print(read_ast_summary(fixed))


if __name__ == "__main__":
    demo_without_git()
