"""Week 5 Day 2 exercise: the Strands worker, run from the terminal.

What this script does, step by step:
  1. Builds the model (Gemini through its OpenAI-compatible endpoint).
  2. Defines three board tools the agent can call.
  3. Connects the filesystem MCP server, limited to the workspace folder.
  4. Seeds the board with a new goal (a haiku about Madrid -> madrid.txt).
  5. Lets the agent loop plan, write the file and tick off its steps.
  6. Prints the finished board and the file the agent wrote.

    uv run strands_exercise_worker.py
"""

import asyncio
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

import board

# Read the API keys from the repo-root .env file.
load_dotenv(override=True)

# The only folder the agent may touch, next to this script.
WORKSPACE = Path(__file__).resolve().parent / "workspace"
OUTPUT_FILE = "madrid.txt"
GOAL = f"Write a short haiku about Madrid into {OUTPUT_FILE}."

# --- Step 1: the model -------------------------------------------------------
# Strands talks to any OpenAI-compatible endpoint, so swapping providers is just
# the base_url and model id. Here we use Gemini. Gemini 3 models fail through this
# endpoint (missing thought_signature on tool calls), so we use a 2.5 model.
# To go back to OpenAI, use:
#   OpenAIModel(client_args={"api_key": os.environ["OPENAI_API_KEY"]}, model_id="gpt-5.4-mini")
model = OpenAIModel(
    client_args={
        "api_key": os.environ["GOOGLE_API_KEY"],
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    model_id="gemini-2.5-flash",
)


# --- Step 2: the board tools -------------------------------------------------
# @tool turns a typed function into a tool: type hints become the argument schema
# and the docstring becomes the description the model reads.
@tool
def show_todos() -> list[dict]:
    """List every todo on the board. A goal has parent_id None; a step has parent_id set to its goal's id."""
    return board.list_todos()


@tool
def plan_steps(goal_id: int, steps: list[str]) -> dict:
    """Break a goal into an ordered checklist of steps on the board.

    Args:
        goal_id: The id of the goal to break down.
        steps: Short descriptions of the steps to take, in order.
    """
    return {"goal_id": goal_id, "step_ids": [board.add_step(goal_id, step) for step in steps]}


@tool
def complete_task(task_id: int, result: str) -> dict:
    """Mark a todo (a step or the goal) done and record a short result summary.

    Args:
        task_id: The id of the todo to mark done.
        result: A short summary of what was accomplished.
    """
    board.complete_todo(task_id, result)
    return {"task_id": task_id, "status": "done"}


# --- Step 3: the filesystem MCP server ---------------------------------------
# MCP gives the agent tools we did not write. The Node filesystem server is started
# as a subprocess and talks to Strands over stdin/stdout. It is scoped to WORKSPACE,
# so the agent cannot read or write anywhere else.
filesystem = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
            cwd=str(WORKSPACE),  # relative names like madrid.txt resolve inside the workspace
        ),
        errlog=subprocess.DEVNULL,  # hide the server's startup logging
    ),
    startup_timeout=60,
)

# The system prompt tells the agent how to behave: plan on the board, do the work
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
    # One agent gets the model, the prompt, our three board tools and the MCP
    # filesystem. Strands runs the loop: pick a tool, read the result, pick again,
    # until the goal is done.
    worker = Agent(
        model=model,
        system_prompt=INSTRUCTIONS,
        tools=[show_todos, plan_steps, complete_task, filesystem],
    )
    await worker.invoke_async("Please work the pending goal on the board.")

    # --- Step 6: show the outcome --------------------------------------------
    print("\nBoard after the run:")
    board.show_board()
    output = WORKSPACE / OUTPUT_FILE
    if output.exists():
        print(f"\n{OUTPUT_FILE}:\n" + output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
