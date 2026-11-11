"""A tiny SQLite todo board: the shared substrate every Week 5 worker uses.

A worker is handed one goal. To reach it, the worker writes its own step todos
under that goal, ticks each one off as it finishes, and marks the goal done once
the steps are complete. Days 1 to 4 each run their own little board like this;
Day 5 the same idea grows into a shared board that coordinates a whole team. The
board is a single file with one table, so it needs no server and behaves the same
on Mac and Windows. WAL mode plus a busy timeout let several agents read and write
at once without tripping over each other.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from rich.console import Console

BOARD_PATH = Path(os.environ.get("BOARD_PATH", Path(__file__).resolve().parent / "board.sqlite"))


def _connect(path: Path = BOARD_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def reset_board(path: Path = BOARD_PATH) -> None:
    """Create a fresh, empty board, dropping anything already there."""
    with _connect(path) as conn:
        conn.execute("DROP TABLE IF EXISTS todos")
        conn.execute(
            """CREATE TABLE todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                task TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT NOT NULL DEFAULT ''
            )"""
        )


def add_goal(task: str, path: Path = BOARD_PATH) -> int:
    """Add a top-level goal to the board and return its id."""
    with _connect(path) as conn:
        cur = conn.execute("INSERT INTO todos (task) VALUES (?)", (task,))
        return cur.lastrowid


def add_step(goal_id: int, task: str, path: Path = BOARD_PATH) -> int:
    """Add a step under a goal and return its id."""
    with _connect(path) as conn:
        cur = conn.execute(
            "INSERT INTO todos (parent_id, task) VALUES (?, ?)", (goal_id, task)
        )
        return cur.lastrowid


def list_todos(path: Path = BOARD_PATH) -> list[dict]:
    """Return every todo on the board, goals and steps, oldest first."""
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT id, parent_id, task, status, result FROM todos ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


def claim_todo(task_id: int, path: Path = BOARD_PATH) -> None:
    """Mark a todo as in progress, so a worker can show it has picked it up."""
    with _connect(path) as conn:
        conn.execute("UPDATE todos SET status = 'in_progress' WHERE id = ?", (task_id,))


def complete_todo(task_id: int, result: str, path: Path = BOARD_PATH) -> None:
    """Mark a todo as done and record its result."""
    with _connect(path) as conn:
        conn.execute(
            "UPDATE todos SET status = 'done', result = ? WHERE id = ?",
            (result, task_id),
        )


def show_board(path: Path = BOARD_PATH) -> None:
    """Print the board for a human: each goal with its steps indented beneath,
    done todos struck through in green and anything in progress in yellow. This
    is just a pretty view; the agent's show_todos tool still gets plain dicts.
    """
    todos = list_todos(path)
    lines = []
    for goal in [t for t in todos if t["parent_id"] is None]:
        lines.append(_format(goal, "Goal", ""))
        for step in [t for t in todos if t["parent_id"] == goal["id"]]:
            lines.append(_format(step, "Step", "  "))
    if lines:
        # Print the whole board in one go. Printing line by line makes a Jupyter
        # kernel emit a separate block per line, which stacks with gaps; soft_wrap
        # keeps a long goal line from wrapping.
        Console().print("\n".join(lines), soft_wrap=True)


def _format(todo: dict, kind: str, indent: str) -> str:
    label = f"{indent}{kind} #{todo['id']}: {todo['task']}"
    if todo["status"] == "done":
        line = f"[green][strike]{label}[/strike][/green]"
        if todo["result"]:
            line += f"  [dim]{todo['result']}[/dim]"
        return line
    if todo["status"] == "in_progress":
        return f"[yellow]{label}[/yellow]"
    return label
