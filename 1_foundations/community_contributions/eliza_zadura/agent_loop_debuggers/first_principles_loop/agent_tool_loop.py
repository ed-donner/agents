# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# <table style="margin: 0; text-align: left; width:100%">
#     <tr>
#         <td>
#             <h2 style="color:#ff7800;">Exercise</h2>
#             <span style="color:#ff7800;">Now try to build an Agent Loop from scratch yourself!<br/>
#             Create a new .ipynb and make one from first principles, referring back to this as needed.<br/>
#             It's one of the few times that I recommend typing from scratch - it's a very satisfying result.
#             </span>
#             <p>
#             Read from the <code>docs_ez/first_principles_loop/buggy_kata</code> folder, which contains a collection of files with bugs in them. Parse test output from the terminal, and use it to fix the bugs. Rerun the tests until they all pass, or until hard stop.
#             </p>
#         </td>
#     </tr>
# </table>

# %% [markdown]
# ## Loop:
#
# **Observe**:
# - run tests
#
# **Select**:
# - parse failures
# - pick one failing test (or pick the first one)
#
#  **Act**:
# - read the relevant file
# - apply the smallest change to fix that failure
#
#  **Verify**:
# - run tests again
# - mark failure resolved or not
#
#  **Terminate**:
# - all tests pass or
# - max iterations reached

# %%
# Start with some imports - rich is a library for making formatted text output in the terminal

from rich.console import Console
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv(override=True)

# %%
TARGET_FOLDER = "buggy_kata"
MAX_ITERATIONS = 15


def reset_buggy_kata():
    """Reset buggy_kata by running the dedicated reset helper."""
    from buggy_kata.reset_kata import reset_buggy_kata_state

    restored_file = reset_buggy_kata_state()
    print(f"✅ Reset complete: {restored_file}")


# %%
# Create a single console instance for consistent output
console = Console()


def show(text):
    """Print formatted text using rich console."""
    try:
        console.print(text)
    except Exception:
        print(text)


# %%
openai = OpenAI()

# %%
import subprocess
import sys
import os
from pathlib import Path

# Get the workspace root (where the notebook is running from)
WORKSPACE_ROOT = Path.cwd()

# Debug: print where we think the workspace is
print(f"WORKSPACE_ROOT: {WORKSPACE_ROOT}")
print(f"Python executable: {sys.executable}")


# tools:
def run_tests(folder_path: str) -> str:
    """
    Run pytest on the tests folder within the target folder.
    Returns combined stdout/stderr output.
    """
    # Resolve to absolute path if relative
    abs_path = Path(folder_path)
    if not abs_path.is_absolute():
        abs_path = WORKSPACE_ROOT / folder_path

    # Use sys.executable to ensure we use the same Python as the notebook
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=str(abs_path),
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    return output


def resolve_code_path(file_path: str) -> Path:
    """
    Resolve tool-provided file paths and tolerate common buggy_kata aliases.
    """
    raw = Path(file_path)
    abs_path = raw if raw.is_absolute() else WORKSPACE_ROOT / raw
    if abs_path.exists():
        return abs_path

    # Common model alias: buggy_kata/utils.py -> buggy_kata/src/utils.py
    rel = abs_path.relative_to(WORKSPACE_ROOT) if abs_path.is_relative_to(WORKSPACE_ROOT) else raw
    rel_str = rel.as_posix()
    if rel_str.startswith("buggy_kata/") and "/src/" not in rel_str:
        alias = WORKSPACE_ROOT / "buggy_kata" / "src" / Path(rel_str).name
        if alias.exists() or alias.parent.exists():
            return alias

    return abs_path


def read_file(file_path: str) -> str:
    """
    Read and return the contents of a file.
    """
    abs_path = resolve_code_path(file_path)

    with open(abs_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file, overwriting any existing content.
    Returns confirmation message.
    """
    abs_path = resolve_code_path(file_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote to {file_path}"


# %%
# tool definitions

run_tests_json = {
    "name": "run_tests",
    "description": "Run pytest in buggy_kata/tests and return pass/fail output with tracebacks.",
    "parameters": {
        "type": "object",
        "properties": {
            "folder_path": {
                "type": "string",
                "description": "Path to the folder containing the tests/ subdirectory",
            }
        },
        "required": ["folder_path"],
        "additionalProperties": False,
    },
}

read_file_json = {
    "name": "read_file",
    "description": "Read and return file contents. For source code, prefer buggy_kata/src/utils.py.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to read. Use buggy_kata/src/utils.py for fixes and buggy_kata/tests/test_utils.py for context.",
            }
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
}

write_file_json = {
    "name": "write_file",
    "description": "Write full content to a file. Only modify buggy_kata/src/utils.py.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to write. Use buggy_kata/src/utils.py.",
            },
            "content": {
                "type": "string",
                "description": "The complete content to write to the file",
            },
        },
        "required": ["file_path", "content"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": run_tests_json},
    {"type": "function", "function": read_file_json},
    {"type": "function", "function": write_file_json},
]

# %%
import re

# Regex to strip ANSI escape codes
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE.sub("", text)


def summarize_test_output(output: str) -> str:
    """Extract a human-friendly summary from pytest output."""
    # Strip ANSI codes first!
    clean = strip_ansi(output)
    lines = clean.strip().split("\n")

    # Find passed/failed counts and failed test names
    failed_tests = []
    passed_count = 0
    failed_count = 0

    for line in lines:
        # Look for the summary line like "7 failed, 8 passed in 0.21s"
        if " passed" in line and ("failed" in line or "==" in line):
            # Extract numbers
            match = re.search(r"(\d+) passed", line)
            if match:
                passed_count = int(match.group(1))
            match = re.search(r"(\d+) failed", line)
            if match:
                failed_count = int(match.group(1))

        # Collect failed test names
        if "FAILED" in line and "::" in line:
            # Extract just the test function name
            parts = line.split("::")
            if len(parts) >= 2:
                test_name = parts[-1].split()[0].split("-")[0]
                if test_name not in failed_tests:
                    failed_tests.append(test_name)

    if failed_count > 0:
        summary = f"{failed_count} failed, {passed_count} passed"
        test_list = ", ".join(failed_tests[:4])
        if len(failed_tests) > 4:
            test_list += f" (+{len(failed_tests) - 4} more)"
        return f"❌ {summary}\n   Failed: {test_list}"
    elif passed_count > 0:
        return f"✅ All {passed_count} tests passed!"
    else:
        # Fallback - just show first few clean lines
        preview = "\n".join(lines[:3])
        return preview if len(preview) < 200 else preview[:200] + "..."


def report_tool_call(tool_name, arguments, result):
    """
    Pretty-print what the agent is doing for each tool call.
    """
    console = Console()

    if tool_name == "run_tests":
        console.print("\n[bold cyan]🧪 Running tests...[/bold cyan]")
        console.print(f"   [dim]folder:[/dim] {arguments.get('folder_path', 'N/A')}")
        # Print summary (already cleaned of ANSI codes)
        summary = summarize_test_output(result)
        for line in summary.split("\n"):
            console.print(f"   {line}")

    elif tool_name == "read_file":
        path = arguments.get("file_path", "unknown")
        lines = result.count("\n") + 1
        console.print(
            f"\n[bold cyan]📖 Reading:[/bold cyan] {path} [dim]({lines} lines)[/dim]"
        )

    elif tool_name == "write_file":
        path = arguments.get("file_path", "unknown")
        content = arguments.get("content", "")
        console.print(
            f"\n[bold cyan]✏️  Writing:[/bold cyan] {path} [dim]({len(content)} chars)[/dim]"
        )
        console.print("   [green]✓ Saved[/green]")

    else:
        console.print(f"\n[bold cyan]▶ {tool_name}[/bold cyan]")
        for key, value in arguments.items():
            display = (
                value[:80] + "..."
                if isinstance(value, str) and len(value) > 80
                else value
            )
            console.print(f"   [dim]{key}:[/dim] {display}")


def handle_tool_calls(tool_calls):
    """
    Execute each tool call and return results in the format expected by OpenAI.
    """
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        # Look up the function by name and call it
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else f"Unknown tool: {tool_name}"

        # Report what happened
        report_tool_call(tool_name, arguments, result)

        results.append(
            {
                "role": "tool",
                "content": result if isinstance(result, str) else json.dumps(result),
                "tool_call_id": tool_call.id,
            }
        )
    return results


# %%
def loop(messages):
    """
    The agent loop: call the model, handle tool calls, repeat until done or max iterations.
    """
    iteration = 0
    done = False
    last_response_id = None

    show("[bold magenta]🤖 Bug-Fixing Agent Started[/bold magenta]")
    show(f"[dim]Target: {TARGET_FOLDER} | Max iterations: {MAX_ITERATIONS}[/dim]\n")

    while not done and iteration < MAX_ITERATIONS:
        iteration += 1
        show(f"[bold blue]━━━ Step {iteration}/{MAX_ITERATIONS} ━━━[/bold blue]")

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            store=True,
            metadata={"run_mode": "with_trace"},
        )
        last_response_id = response.id

        finish_reason = response.choices[0].finish_reason
        message = response.choices[0].message

        if finish_reason == "tool_calls":
            # Model wants to call tools
            tool_calls = message.tool_calls

            # Execute tools and get results
            results = handle_tool_calls(tool_calls)

            # Add assistant message and tool results to conversation
            messages.append(message)
            messages.extend(results)
        else:
            # Model is done (finish_reason == "stop")
            done = True
            show("\n[bold green]✅ Agent Complete![/bold green]")
            show(f"[dim]Finished in {iteration} steps[/dim]\n")
            if message.content:
                show("[bold]Summary:[/bold]")
                show(message.content)

            # Surface trace/log lookup details at the end of each run
            if last_response_id:
                show(f"[dim]Trace ID: {last_response_id}[/dim]")
                show(
                    f"[dim]View trace: https://platform.openai.com/logs?api=chat-completions&id={last_response_id}[/dim]"
                )
            else:
                show("[dim]View traces: https://platform.openai.com/logs?api=chat-completions[/dim]")

    if iteration >= MAX_ITERATIONS:
        show(f"\n[bold red]⚠️  Reached max iterations ({MAX_ITERATIONS})[/bold red]")

    return messages


# %%
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


def format_conversation(messages, show_system=False):
    """
    Display a human-readable summary of the agent conversation.

    Args:
        messages: The messages list from the agent loop
        show_system: Whether to show the system prompt (default False)
    """
    console = Console()

    for msg in messages:
        # Handle dict messages (user, system, tool results)
        if isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "system":
                if show_system:
                    console.print(
                        Panel(
                            content[:300] + "..." if len(content) > 300 else content,
                            title="[bold blue]System[/bold blue]",
                            border_style="blue",
                        )
                    )

            elif role == "user":
                console.print(
                    Panel(
                        content,
                        title="[bold green]User[/bold green]",
                        border_style="green",
                    )
                )

            elif role == "tool":
                # Tool results - show a compact summary
                clean = strip_ansi(content)
                if "passed" in clean or "failed" in clean:
                    # Test output - show summary only
                    summary = summarize_test_output(content)
                    console.print(
                        f"   [dim]Tool result:[/dim] {summary.split(chr(10))[0]}"
                    )
                elif len(clean) > 150:
                    console.print(f"   [dim]Tool result:[/dim] ({len(clean)} chars)")
                else:
                    console.print(f"   [dim]Tool result:[/dim] {clean[:100]}")

        # Handle ChatCompletionMessage objects (assistant responses)
        elif hasattr(msg, "role") and msg.role == "assistant":
            if msg.tool_calls:
                # Show tool calls in a compact format
                calls = [
                    f"{tc.function.name}({list(json.loads(tc.function.arguments).values())[0] if tc.function.arguments != '{}' else ''})"
                    for tc in msg.tool_calls
                ]
                console.print(
                    f"\n[bold yellow]🤖 Agent:[/bold yellow] {', '.join(calls)}"
                )
            elif msg.content:
                console.print(
                    Panel(
                        msg.content,
                        title="[bold yellow]🤖 Agent[/bold yellow]",
                        border_style="yellow",
                    )
                )


def show_summary(messages):
    """Show a quick stats summary of the conversation."""
    console = Console()

    tool_counts = {}
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.function.name
                tool_counts[name] = tool_counts.get(name, 0) + 1

    table = Table(title="Agent Run Summary", show_header=True)
    table.add_column("Tool", style="cyan")
    table.add_column("Calls", style="green", justify="right")

    for tool, count in sorted(tool_counts.items()):
        table.add_row(tool, str(count))

    table.add_row("[bold]Total[/bold]", f"[bold]{sum(tool_counts.values())}[/bold]")
    console.print(table)


# %%
system_message = f"""
You are given a buggy kata. Fix failing tests with minimal edits.

Target folder: {TARGET_FOLDER}

Important constraints:
- Run tests from {TARGET_FOLDER}.
- Read tests from {TARGET_FOLDER}/tests/test_utils.py when needed.
- Only edit {TARGET_FOLDER}/src/utils.py.
- Do not edit files outside {TARGET_FOLDER}/src/utils.py.
"""

messages = [
    {"role": "system", "content": system_message},
    {
        "role": "user",
        "content": "Please fix all failing tests with trace. Start by running tests, then only edit buggy_kata/src/utils.py.",
    },
]

# %% [markdown]
# system_message = f"""
# You are a bug-fixing agent. Your goal is to fix all failing tests in the codebase.
#
# Target folder: {TARGET_FOLDER}
#
# Your workflow:
# 1. Run the tests to see what's failing
# 2. Read the relevant source file to understand the bug
# 3. Write the corrected file to fix the bug
# 4. Repeat until all tests pass
#
# Important:
# - Fix one bug at a time, then re-run tests to verify
# - Make minimal changes - only fix what's broken
# - The source files are in {TARGET_FOLDER}/src/
# - Do not modify the test files
# """
#
# messages = [
#     {"role": "system", "content": system_message},
#     {
#         "role": "user",
#         "content": "Please fix all failing tests with trace. Start by running tests, then only edit buggy_kata/src/utils.py.",
#     },
# ]

# %%
# Run the agent loop!
result = loop(messages)

# Suppress the raw messages output by assigning to a variable
# To see a formatted conversation history, run: format_conversation(result)
# To see stats, run: show_summary(result)

# %%
# Optional: View a formatted conversation summary
format_conversation(result)

# Optional: View tool usage stats
show_summary(result)

# %%
# Reset command (no uncommenting needed):
# python buggy_kata/reset_kata.py
