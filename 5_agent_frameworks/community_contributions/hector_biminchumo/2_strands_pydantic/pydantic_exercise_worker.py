"""Week 5 Day 2 exercise: the Pydantic AI worker, run from the terminal.

What this script does, step by step:
  1. Picks the model.
  2. Defines three board tools the agent can call.
  3. Connects the filesystem MCP server, limited to the workspace folder.
  4. Seeds the board with a new goal (a haiku about Madrid -> madrid.txt).
  5. Lets the agent loop plan, write the file and tick off its steps.
  6. Prints the finished board, the file, and the full message transcript.

    uv run pydantic_exercise_worker.py
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from fastmcp.client.transports import StdioTransport

import board

# Read the API keys from the repo-root .env file.
load_dotenv(override=True)

# The only folder the agent may touch, next to this script.
WORKSPACE = Path(__file__).resolve().parent / "workspace"
OUTPUT_FILE = "madrid.txt"
GOAL = f"Write a short haiku about Madrid into {OUTPUT_FILE}."

# --- Step 1: the model -------------------------------------------------------
# Pydantic AI takes the provider and model as one string.
MODEL = "openai-chat:gpt-5.4-mini"


# --- Step 2: the board tools -------------------------------------------------
# Plain typed functions. Pydantic AI builds the argument schema from the type hints
# and the tool description from the docstring.
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


# --- Step 3: the filesystem MCP server ---------------------------------------
# MCP gives the agent tools we did not write. StdioTransport starts the Node
# filesystem server as a subprocess and talks to it over stdin/stdout. It is scoped
# to WORKSPACE, so the agent cannot read or write anywhere else.
filesystem = MCPToolset(
    StdioTransport(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
        cwd=str(WORKSPACE),  # relative names like madrid.txt resolve inside the workspace
        log_file=Path(os.devnull),  # hide the server's startup logging
    ),
    init_timeout=60,
)

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

    # --- Step 5: the agent loop ----------------------------------------------
    # Python functions go in tools=[...]; the MCP server goes in toolsets=[...].
    worker = Agent(
        MODEL,
        instructions=INSTRUCTIONS,
        tools=[show_todos, plan_steps, complete_task],
        toolsets=[filesystem],
    )
    # `async with worker` opens the connection to the MCP server for the run
    # and closes it afterwards.
    async with worker:
        result = await worker.run("Please work the pending goal on the board.")
    print(result.output)

    # --- Step 6: show the outcome --------------------------------------------
    print("\nBoard after the run:")
    board.show_board()
    output = WORKSPACE / OUTPUT_FILE
    if output.exists():
        print(f"\n{OUTPUT_FILE}:\n" + output.read_text(encoding="utf-8"))

    # The full transcript: the prompt, every tool call the loop made and every
    # result it read back, ending with the model's final answer.
    print("\nTranscript (result.all_messages()):")
    for message in result.all_messages():
        for part in message.parts:
            print(f"{type(part).__name__}: {part}")
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
