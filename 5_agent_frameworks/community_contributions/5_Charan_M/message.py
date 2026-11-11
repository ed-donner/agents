from smolagents import CodeAgent, LiteLLMModel
from dotenv import load_dotenv

load_dotenv()

# Step 2: Run it - send a message, get a reply
model = LiteLLMModel(model_id="gemini/gemini-2.5-flash")

agent = CodeAgent(
    tools=[],
    model=model,
    add_base_tools=False
)

print("Sending message...")
response = agent.run("Please say a short greeting in Spanish.")
print(f"Reply: {response}")
