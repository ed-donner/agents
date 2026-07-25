from typing import Any

from mcp.server.fastmcp import FastMCP

from config import TASKS_FILE, iso_today
from task_store import TaskStore


STORE = TaskStore(TASKS_FILE)
MCP = FastMCP("personal_task_coach_server")


@MCP.tool()
async def create_task(
    title: str,
    description: str,
    due_date: str,
    estimated_minutes: int = 30,
    difficulty: int = 2,
) -> dict[str, Any]:
    """Create a task for a specific due value.

    Args:
        title: Short task title
        description: Action-focused task details
        due_date: Due date in YYYY-MM-DD, or datetime in ISO format
        estimated_minutes: Estimated effort in minutes
        difficulty: Relative task difficulty from 1 (easy) to 5 (hard)
    """
    return STORE.create_task(title, description, due_date, estimated_minutes, difficulty)


@MCP.tool()
async def update_task_status(task_id: str, status: str, blocker: str = "") -> dict[str, Any]:
    """Update task status.

    Args:
        task_id: Task identifier (e.g. task-abc12345)
        status: One of pending, done, missed, skipped
        blocker: Optional reason if task is missed or skipped
    """
    return STORE.update_task_status(task_id, status, blocker)


@MCP.tool()
async def get_today_tasks(target_date: str = "") -> list[dict[str, Any]]:
    """Get tasks for today, or a specified date.

    Args:
        target_date: Optional date in YYYY-MM-DD, or datetime in ISO format
    """
    selected_date = target_date.strip() or iso_today()
    return STORE.get_tasks_by_date(selected_date)


if __name__ == "__main__":
# def run_task_server() -> None:
    MCP.run(transport="stdio")
