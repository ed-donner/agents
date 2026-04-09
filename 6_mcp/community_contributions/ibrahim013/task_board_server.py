"""stdio MCP server: task board persisted as JSON."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("task_board_server")

_PRIORITIES = frozenset({"low", "medium", "high"})
_STATUSES = frozenset({"open", "done"})


def _tasks_path() -> Path:
    override = os.environ.get("TASKS_JSON_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent / "tasks.json"


def _load_tasks() -> list[dict]:
    path = _tasks_path()
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("tasks.json must contain a JSON array")
    return data


def _save_tasks(tasks: list[dict]) -> None:
    path = _tasks_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def _find_task(tasks: list[dict], task_id: str) -> tuple[list[dict], int | None]:
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            return tasks, i
    return tasks, None


@mcp.tool()
async def add_task(
    title: str,
    description: str = "",
    priority: str = "medium",
) -> dict:
    """Add a new open task to the board.

    Args:
        title: Short title for the task.
        description: Optional longer description.
        priority: One of low, medium, high (default medium).
    """
    if priority not in _PRIORITIES:
        return {"error": f"priority must be one of {sorted(_PRIORITIES)}", "priority": priority}
    tasks = _load_tasks()
    task = {
        "id": str(uuid.uuid4()),
        "title": title.strip(),
        "description": (description or "").strip(),
        "status": "open",
        "priority": priority,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tasks.append(task)
    _save_tasks(tasks)
    return task


@mcp.tool()
async def list_tasks(status_filter: str | None = None) -> list[dict]:
    """List tasks, optionally filtered by status.

    Args:
        status_filter: If set, only 'open' or 'done' tasks; if omitted, return all.
    """
    if status_filter is not None and status_filter not in _STATUSES:
        return [{"error": f"status_filter must be one of {sorted(_STATUSES)} or null"}]
    tasks = _load_tasks()
    if status_filter is None:
        return list(tasks)
    return [t for t in tasks if t.get("status") == status_filter]


@mcp.tool()
async def complete_task(task_id: str) -> dict:
    """Mark a task as done. Idempotent if already done.

    Args:
        task_id: The task id returned by add_task.
    """
    tasks = _load_tasks()
    _, idx = _find_task(tasks, task_id)
    if idx is None:
        return {"ok": False, "error": f"unknown task_id: {task_id}"}
    if tasks[idx].get("status") == "done":
        return {"ok": True, "task": tasks[idx], "note": "already complete"}
    tasks[idx]["status"] = "done"
    tasks[idx]["completed_at"] = datetime.now(timezone.utc).isoformat()
    _save_tasks(tasks)
    return {"ok": True, "task": tasks[idx]}


@mcp.tool()
async def set_priority(task_id: str, priority: str) -> dict:
    """Change priority for a task.

    Args:
        task_id: The task id.
        priority: One of low, medium, high.
    """
    if priority not in _PRIORITIES:
        return {"ok": False, "error": f"priority must be one of {sorted(_PRIORITIES)}"}
    tasks = _load_tasks()
    _, idx = _find_task(tasks, task_id)
    if idx is None:
        return {"ok": False, "error": f"unknown task_id: {task_id}"}
    tasks[idx]["priority"] = priority
    _save_tasks(tasks)
    return {"ok": True, "task": tasks[idx]}


@mcp.resource("taskboard://snapshot")
async def read_taskboard_snapshot() -> str:
    """Full task list as pretty-printed JSON (debugging / inspection)."""
    tasks = _load_tasks()
    return json.dumps(tasks, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
