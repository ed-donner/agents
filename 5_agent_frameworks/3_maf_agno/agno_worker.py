"""Run the Day 3 Agno worker against the board as a plain subprocess.

Seeds one goal ("read notes.txt, translate to Spanish, write spanish.txt"), then
lets the Agno agent loop work it: plan the steps on the board, read the file through
the filesystem MCP server, translate, write the Spanish back, and tick each step off
before closing the goal. This is the same worker the notebook builds in step 5,
packaged as a script you can run from the terminal. It is also the shape every
worker takes on Day 5.

    uv run agno_worker.py
"""

from __future__ import annotations

import asyncio
import functools
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

# Agno's MCP tools do not expose the server's stderr, so we point its stdio client
# at DEVNULL. That quiets the filesystem server's startup banner and lets it run
# from a Jupyter kernel on Windows. It is the same fix every framework needs this week.
import agno.tools.mcp.mcp as agno_mcp

agno_mcp.stdio_client = functools.partial(agno_mcp.stdio_client, errlog=subprocess.DEVNULL)

import board  # noqa: E402

load_dotenv(override=True)

MODEL = "gpt-5.4-mini"
WORKSPACE = Path(__file__).resolve().parent / "workspace"
GOAL = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt."

model = OpenAIChat(id=MODEL)


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
    goal_id = seed()
    print(f"Seeded goal {goal_id}: {GOAL}\n")

    server = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
        cwd=str(WORKSPACE),
    )
    async with MCPTools(server_params=server) as filesystem:
        worker = Agent(
            model=model,
            instructions=INSTRUCTIONS,
            tools=[show_todos, plan_steps, complete_task, filesystem],
        )
        await worker.arun(input="Please work the pending goal on the board.")

    print("\nBoard after the run:")
    board.show_board()

    spanish = WORKSPACE / "spanish.txt"
    if spanish.exists():
        print("\nspanish.txt:\n" + spanish.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
