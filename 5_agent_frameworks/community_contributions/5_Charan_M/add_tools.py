from smolagents import CodeAgent, LiteLLMModel
from dotenv import load_dotenv
from tools import show_todos, plan_steps, complete_task
from board import add_goal, reset_board

load_dotenv()

# Step 3: Add tools
reset_board()
add_goal("Write a short haiku about Madrid into madrid.txt.")

model = LiteLLMModel(model_id="gemini/gemini-2.5-flash")

agent = CodeAgent(
    tools=[show_todos, plan_steps, complete_task],
    model=model,
    add_base_tools=False
)

print("Agent is checking the board...")
response = agent.run("Use your tools to find out what is on the board right now, then tell me.")
print(f"Reply: {response}")
