from smolagents import CodeAgent, LiteLLMModel
from dotenv import load_dotenv

load_dotenv()

# Step 1: Create the agent
model = LiteLLMModel(model_id="gemini/gemini-2.5-flash")

agent = CodeAgent(
    tools=[],
    model=model,
    add_base_tools=False,
    system_prompt="You are a helpful AI assistant."
)

print("Created agent: Assistant")
