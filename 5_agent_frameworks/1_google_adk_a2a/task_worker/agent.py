"""The Day 1 worker agent: one LlmAgent that works the SQLite board.

The same agent runs three ways: visually with `adk web`, in the terminal with
`adk run`, or driven from worker.py as a plain subprocess. The board tools give
it its task, the filesystem MCP server gives it files, and the agent loop does
the rest. Days 2 to 4 rebuild this exact contract in a different framework.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from quiet import silence

silence()

from dotenv import load_dotenv  # noqa: E402

import board  # noqa: E402

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams  # noqa: E402
from mcp import StdioServerParameters  # noqa: E402

load_dotenv(override=True)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

MODEL = "gemini-3.1-flash-lite"
WORKSPACE = Path(__file__).resolve().parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)


def show_todos() -> list[dict]:
    """List every todo on the board. A goal has parent_id None; a step has parent_id set to its goal's id."""
    return board.list_todos()


def plan_steps(goal_id: int, steps: list[str]) -> dict:
    """Break a goal into an ordered checklist of steps on the board. Pass the goal's id and a short list of step descriptions."""
    step_ids = [board.add_step(goal_id, step) for step in steps]
    return {"goal_id": goal_id, "step_ids": step_ids}


def complete_task(task_id: int, result: str) -> dict:
    """Mark a todo (a step or the goal) with this id as done and record a short result summary."""
    board.complete_todo(task_id, result)
    return {"task_id": task_id, "status": "done"}


# The filesystem MCP server runs over npx and is scoped to the workspace folder,
# so the agent can only touch files inside it. This is the same server wired the
# same way in every framework this week.
filesystem = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
            cwd=str(WORKSPACE),  # start the server in the workspace so relative file names resolve there
        ),
        timeout=60
    ),
    # Send the server's stderr to DEVNULL. This quiets its startup logging, and
    # it is also what lets the notebook spawn this server from a Jupyter kernel
    # on Windows, where the kernel's stderr has no real file descriptor.
    errlog=subprocess.DEVNULL,
)

INSTRUCTIONS = """
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
"""

root_agent = LlmAgent(
    model=MODEL,
    name="task_worker",
    description="Works one goal from the SQLite board using its files.",
    instruction=INSTRUCTIONS,
    tools=[show_todos, plan_steps, complete_task, filesystem],
)
