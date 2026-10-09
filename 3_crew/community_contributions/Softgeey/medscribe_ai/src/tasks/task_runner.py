"""
Task definitions for the MedScribe AI engineering crew.
Each task wraps one agent call and passes output to the next stage.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class TaskResult:
    task_name: str
    agent_name: str
    output: str
    success: bool
    error: str = ""


def run_task(task_name: str, agent_name: str, agent_fn: Callable, *args) -> TaskResult:
    """
    Execute a single agent task safely.
    Returns a TaskResult — never raises, so the crew can handle failures gracefully.
    """
    try:
        output = agent_fn(*args)
        return TaskResult(
            task_name=task_name,
            agent_name=agent_name,
            output=output,
            success=True,
        )
    except Exception as exc:
        return TaskResult(
            task_name=task_name,
            agent_name=agent_name,
            output="",
            success=False,
            error=str(exc),
        )
