from smolagents import CodeAgent, LiteLLMModel
from dotenv import load_dotenv
from tools import show_todos, plan_steps, complete_task
from add_mcp import read_file, write_file
from board import add_goal, reset_board
from pathlib import Path

load_dotenv()

# Step 5: Put it in a loop with a goal
reset_board()
goal_id = add_goal("Write a short haiku about Madrid into madrid.txt.")

INSTRUCTIONS = """
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: 
the handful of concrete steps the work itself breaks down into, added to the board under the goal. 
Then carry them out with your file tools, marking each step done as you finish it. 
Once the steps are all done, close the goal.
"""

model = LiteLLMModel(model_id="gemini/gemini-2.5-flash")

agent = CodeAgent(
    tools=[show_todos, plan_steps, complete_task, read_file, write_file],
    model=model,
    add_base_tools=False,
    system_prompt=INSTRUCTIONS
)

print("Starting the agent loop on the goal...")
response = agent.run("Please work the pending goal on the board.")

print("\nFinal board state:")
from board import get_board_summary
print(get_board_summary())

madrid_file = Path("workspace/madrid.txt")
if madrid_file.exists():
    print(f"\nmadrid.txt contents:\n{madrid_file.read_text(encoding='utf-8')}")

print(f"\nFinal Reply: {response}")
