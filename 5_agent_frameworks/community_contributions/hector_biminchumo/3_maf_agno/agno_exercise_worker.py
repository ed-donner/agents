"""Week 5 Day 3 exercise: the Agno worker, run from the terminal.

What this script does, step by step:
  1. Builds the model.
  2. Defines three board tools the agent can call.
  3. Connects the filesystem MCP server, limited to the workspace folder.
  4. Seeds the board with a new goal (a haiku about Madrid -> madrid.txt).
  5. Lets the agent loop plan, write the file and tick off its steps, printing
     the tool-calling loop live with aprint_response(stream=True).
  6. Prints the finished board and the file the agent wrote.

    uv run agno_exercise_worker.py
"""

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
# at DEVNULL. That keeps the filesystem server's startup logging off the screen.
import agno.tools.mcp.mcp as agno_mcp

agno_mcp.stdio_client = functools.partial(agno_mcp.stdio_client, errlog=subprocess.DEVNULL)

import board

# Read the API keys from the repo-root .env file.
load_dotenv(override=True)

# The only folder the agent may touch, next to this script.
WORKSPACE = Path(__file__).resolve().parent / "workspace"
OUTPUT_FILE = "madrid.txt"
GOAL = f"Write a short haiku about Madrid into {OUTPUT_FILE}."

# --- Step 1: the model -------------------------------------------------------
model = OpenAIChat(id="gpt-5.4-mini")  # reads OPENAI_API_KEY from the environment


# --- Step 2: the board tools -------------------------------------------------
# Plain typed functions. Agno builds the argument schema from the type hints and
# the tool description from the docstring.
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


# The instructions tell the agent how to behave: plan on the board, do the work
# with the file tools, tick off each step, then close the goal.
INSTRUCTIONS = """
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
"""


def seed() -> int:
    """Step 4: reset the board, remove old output and add the goal."""
    board.reset_board()
    WORKSPACE.mkdir(exist_ok=True)
    (WORKSPACE / OUTPUT_FILE).unlink(missing_ok=True)
    goal_id = board.add_goal(GOAL)
    board.claim_todo(goal_id)  # the worker picks up the goal: pending -> in_progress
    return goal_id


async def main() -> None:
    goal_id = seed()
    print(f"Seeded goal {goal_id}: {GOAL}\n")

    # --- Step 3: the filesystem MCP server -----------------------------------
    # MCP gives the agent tools we did not write. The Node filesystem server is
    # started as a subprocess and talks to Agno over stdin/stdout. It is scoped to
    # WORKSPACE, so the agent cannot read or write anywhere else.
    server = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
        cwd=str(WORKSPACE),  # relative names like madrid.txt resolve inside the workspace
    )

    # --- Step 5: the agent loop ----------------------------------------------
    # `async with MCPTools(...)` opens the connection to the MCP server for the run
    # and closes it afterwards. The agent gets our three board tools plus the MCP
    # tools in the same tools=[...] list.
    async with MCPTools(server_params=server, timeout_seconds=60) as filesystem:
        worker = Agent(
            model=model,
            instructions=INSTRUCTIONS,
            tools=[show_todos, plan_steps, complete_task, filesystem],
        )
        # aprint_response(stream=True) prints each tool call and its result live,
        # instead of arun, which only returns the final result at the end.
        await worker.aprint_response(input="Please work the pending goal on the board.", stream=True)

    # --- Step 6: show the outcome --------------------------------------------
    print("\nBoard after the run:")
    board.show_board()
    output = WORKSPACE / OUTPUT_FILE
    if output.exists():
        print(f"\n{OUTPUT_FILE}:\n" + output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
