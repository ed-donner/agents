"""Run the Microsoft Agent Framework worker against the board as a subprocess.

Run bare, it seeds and works its own Day 3 goal (read notes.txt, translate to
Spanish, write spanish.txt): plan the steps on the board, read the file through the
filesystem MCP server, translate, write the Spanish back, and tick each step off
before closing the goal.

Given a task id and a shared board path, the same worker joins the Day 5 agent loop
instead: it points its board and file tools at the shared board and site, claims that
one task, builds what the task asks, and exits, leaving the rest of the board alone.

    uv run maf_worker.py                       # standalone Day 3 demo
    uv run maf_worker.py <taskId> <boardPath>  # Day 5: work one task on a shared board
"""

from __future__ import annotations

import asyncio
import os
import sys
import warnings
from pathlib import Path

# Day 5 mode is "<taskId> <boardPath>". Read it before importing board, because the
# board picks its file from BOARD_PATH at import. Run bare, none of this fires.
TASK_ID = int(sys.argv[1]) if len(sys.argv) > 2 else None
if TASK_ID is not None:
    os.environ.setdefault("BOARD_PATH", sys.argv[2])

warnings.filterwarnings("ignore", message=r".*experimental.*")  # quiet MAF's import-time notices

from dotenv import load_dotenv  # noqa: E402
from agent_framework import Agent, MCPStdioTool  # noqa: E402
from agent_framework.openai import OpenAIChatClient  # noqa: E402

import board  # noqa: E402

load_dotenv(override=True)

MODEL = os.environ.get("WORKER_MODEL", "gpt-5.4-mini")
WORKSPACE = Path(__file__).resolve().parent / "workspace"
GOAL = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt."
# Where the file tools may write: this worker's own workspace when standalone, or
# the shared site (the board file's folder) when working a Day 5 task.
WORK_DIR = WORKSPACE if TASK_ID is None else Path(sys.argv[2]).resolve().parent

client = OpenAIChatClient(model=MODEL)


def show_todos() -> list[dict]:
    """List every todo on the board. A goal has parent_id None; a step has parent_id set to its goal's id."""
    return board.list_todos()


def plan_steps(goal_id: int, steps: list[str]) -> dict:
    """Break a goal into an ordered checklist of steps on the board. Pass the goal's id and a short list of step descriptions."""
    return {"goal_id": goal_id, "step_ids": [board.add_step(goal_id, step) for step in steps]}


def complete_task(task_id: int, result: str) -> dict:
    """Mark a todo (a step or the goal) with this id as done and record a short result summary."""
    board.complete_todo(task_id, result)
    return {"task_id": task_id, "status": "done"}


INSTRUCTIONS = """
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
"""


def seed() -> int:
    """Reset the board, clear any old output, and add the one goal."""
    board.reset_board()
    WORKSPACE.mkdir(exist_ok=True)
    (WORKSPACE / "spanish.txt").unlink(missing_ok=True)
    goal_id = board.add_goal(GOAL)
    board.claim_todo(goal_id)  # the worker picks up the goal: pending -> in_progress
    return goal_id


async def main() -> None:
    if TASK_ID is None:
        goal_id = seed()
        print(f"Seeded goal {goal_id}: {GOAL}\n")
        message = "Please work the pending goal on the board."
    else:
        board.claim_todo(TASK_ID)  # light up this one task on the shared board
        message = (
            f"You have claimed task #{TASK_ID} on the shared board. Work only that task and its steps. "
            f"When the work is built and checked, mark task #{TASK_ID} itself done with complete_task, then stop."
        )

    filesystem = MCPStdioTool(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORK_DIR)],
        cwd=str(WORK_DIR),  # start the server in the work dir so relative file names resolve there
    )
    async with filesystem:
        worker = Agent(
            client=client,
            instructions=INSTRUCTIONS,
            tools=[show_todos, plan_steps, complete_task, filesystem],
        )
        await worker.run(message)

    if TASK_ID is None:  # standalone: show the result; on Day 5 the orchestrator owns the console
        print("\nBoard after the run:")
        board.show_board()
        spanish = WORKSPACE / "spanish.txt"
        if spanish.exists():
            print("\nspanish.txt:\n" + spanish.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
