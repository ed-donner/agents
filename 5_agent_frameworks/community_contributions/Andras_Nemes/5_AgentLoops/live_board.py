"""The live board: a rich.Live view of the shared board while the team works.

Each game is drawn in its owner's colour, with the steps that worker writes for
itself indented beneath in the same colour. Done items are dimmed and struck
through, the one in progress is bold, pending is plain. A small legend maps colour
to framework. The colour comes from the orchestrator's registry (goal id -> worker),
so the board schema and the workers stay untouched: a worker never needs to know
its own colour.
"""

from __future__ import annotations

from rich.console import Console, Group
from rich.text import Text

import board

console = Console()


def _line(todo: dict, colour: str, label: str, indent: str = "") -> Text:
    text = Text(indent)
    if todo["status"] == "done":
        text.append(label, style=f"{colour} dim strike")
        if todo["result"]:
            text.append(f"   {todo['result']}", style="dim")
    elif todo["status"] == "in_progress":
        text.append(label, style=f"bold {colour}")
    else:
        text.append(label, style=colour)
    return text


def render(registry: dict[int, dict]) -> Group:
    """Build the whole board as one renderable from the current board state."""
    todos = board.list_todos()
    children: dict[int | None, list[dict]] = {}
    for todo in todos:
        children.setdefault(todo["parent_id"], []).append(todo)

    lines: list[Text] = []
    for goal in children.get(None, []):
        worker = registry.get(goal["id"])
        colour = worker["colour"] if worker else "white"
        if worker:
            objective = worker.get("objective")
            label = f"{worker['name']}: {objective}" if objective else worker["name"]
        else:
            label = goal["task"][:48]
        lines.append(_line(goal, colour, label))
        for step in children.get(goal["id"], []):
            lines.append(_line(step, colour, step["task"], indent="    "))

    legend = Text("\n")
    seen = set()
    for worker in registry.values():
        if worker["name"] in seen:  # a fixed worker is registered twice; show it once
            continue
        seen.add(worker["name"])
        legend.append(f"{worker['name']}  ", style=worker["colour"])
    lines.append(legend)
    return Group(*lines)
