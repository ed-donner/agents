"""Week 5 Day 3 exercise: the Microsoft Agent Framework worker, run from the terminal.

What this script does, step by step:
  1. Picks the model client (OpenAI, or Gemini through its OpenAI-compatible endpoint).
  2. Defines three board tools the agent can call.
  3. Connects the filesystem MCP server, limited to the workspace folder.
  4. Seeds the board with a new goal (a haiku about Madrid -> madrid.txt).
  5. Lets the agent loop plan, write the file and tick off its steps.
  6. Prints the finished board and the file the agent wrote.

    uv run maf_exercise_worker.py            # OpenAI (gpt-5.4-mini)
    uv run maf_exercise_worker.py gemini     # same agent on Gemini
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path

# The framework prints a couple of "experimental" notices on import; quiet them.
warnings.filterwarnings("ignore", message=r".*experimental.*")

from dotenv import load_dotenv  # noqa: E402
from agent_framework import Agent, MCPStdioTool  # noqa: E402
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient  # noqa: E402

import board  # noqa: E402

# Read the API keys from the repo-root .env file.
load_dotenv(override=True)

# The only folder the agent may touch, next to this script.
WORKSPACE = Path(__file__).resolve().parent / "workspace"
OUTPUT_FILE = "madrid.txt"
GOAL = f"Write a short haiku about Madrid into {OUTPUT_FILE}."

# --- Step 1: the model client ------------------------------------------------
# Part 1 of the exercise runs on OpenAI. Part 2 swaps only the client: same agent,
# same tools, a different model behind an OpenAI-compatible base_url.
PROVIDER = sys.argv[1] if len(sys.argv) > 1 else "openai"

if PROVIDER == "gemini":
    # Gemini only speaks the Chat Completions API, so we use the Chat Completions
    # client here. (OpenAIChatClient calls the Responses API and would get a 404.)
    # Gemini 3 models fail on tool calls this way (missing thought_signature), so
    # we use a 2.5 model.
    client = OpenAIChatCompletionClient(
        model="gemini-2.5-flash",
        api_key=os.environ["GOOGLE_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
else:
    client = OpenAIChatClient(model="gpt-5.4-mini")  # reads OPENAI_API_KEY from the environment


# --- Step 2: the board tools -------------------------------------------------
# Plain typed functions. The framework builds the argument schema from the type
# hints and the tool description from the docstring.
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
    print(f"Seeded goal {goal_id} (provider: {PROVIDER}): {GOAL}\n")

    # --- Step 3: the filesystem MCP server -----------------------------------
    # MCP gives the agent tools we did not write. MCPStdioTool starts the Node
    # filesystem server as a subprocess and talks to it over stdin/stdout. It is
    # scoped to WORKSPACE, so the agent cannot read or write anywhere else.
    filesystem = MCPStdioTool(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
        cwd=str(WORKSPACE),  # relative names like madrid.txt resolve inside the workspace
    )

    # --- Step 5: the agent loop ----------------------------------------------
    # `async with filesystem` opens the connection to the MCP server for the run
    # and closes it afterwards. The agent gets our three board tools plus the MCP
    # tool in the same tools=[...] list, then the framework runs the loop: pick a
    # tool, read the result, pick again, until the goal is done.
    async with filesystem:
        worker = Agent(
            client=client,
            instructions=INSTRUCTIONS,
            tools=[show_todos, plan_steps, complete_task, filesystem],
        )
        await worker.run("Please work the pending goal on the board.")

    # --- Step 6: show the outcome --------------------------------------------
    print("\nBoard after the run:")
    board.show_board()
    output = WORKSPACE / OUTPUT_FILE
    if output.exists():
        print(f"\n{OUTPUT_FILE}:\n" + output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
