"""Run the Day 3 Microsoft Agent Framework worker against the board as a subprocess.

Seeds one goal ("read notes.txt, translate to Spanish, write spanish.txt"), then
lets the MAF agent loop work it: plan the steps on the board, read the file through
the filesystem MCP server, translate, write the Spanish back, and tick each step off
before closing the goal. This is the same worker the notebook builds in step 5,
packaged as a script you can run from the terminal. It is also the shape every
worker takes on Day 5.

    uv run maf_worker.py
"""

from __future__ import annotations

import asyncio
import subprocess
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=r".*experimental.*")  # quiet MAF's import-time notices

from dotenv import load_dotenv  # noqa: E402
from agent_framework import Agent, MCPStdioTool  # noqa: E402
from agent_framework.openai import OpenAIChatClient  # noqa: E402

import board  # noqa: E402

load_dotenv(override=True)

MODEL = "gpt-5.4-mini"
WORKSPACE = Path(__file__).resolve().parent / "workspace"
GOAL = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt."

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


class FilesystemMCP(MCPStdioTool):
    """The filesystem MCP server with its stderr sent to DEVNULL and its working
    directory set to the workspace.

    MAF's MCPStdioTool does not expose the server's stderr, so we override the one
    method that builds the stdio client. errlog=DEVNULL quiets the server's startup
    banner and lets it run from a Jupyter kernel on Windows; cwd starts the server in
    the workspace, so the agent's file names resolve there.
    """

    def get_mcp_client(self):
        from mcp.client.stdio import StdioServerParameters, stdio_client

        params = StdioServerParameters(
            command=self.command, args=self.args, env=self.env, cwd=str(WORKSPACE)
        )
        return stdio_client(server=params, errlog=subprocess.DEVNULL)


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

    filesystem = FilesystemMCP(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
    )
    async with filesystem:
        worker = Agent(
            client=client,
            instructions=INSTRUCTIONS,
            tools=[show_todos, plan_steps, complete_task, filesystem],
        )
        await worker.run("Please work the pending goal on the board.")

    print("\nBoard after the run:")
    board.show_board()

    spanish = WORKSPACE / "spanish.txt"
    if spanish.exists():
        print("\nspanish.txt:\n" + spanish.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
