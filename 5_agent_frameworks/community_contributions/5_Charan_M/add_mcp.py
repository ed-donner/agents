import os
from smolagents import CodeAgent, LiteLLMModel, tool
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Step 4: Add MCP (or in this case, file tools)
WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)

@tool
def read_file(filename: str) -> str:
    """Reads the contents of a file in the workspace.
    
    Args:
        filename: The name of the file to read.
    """
    path = WORKSPACE / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"File {filename} not found."

@tool
def write_file(filename: str, content: str) -> str:
    """Writes content to a file in the workspace.
    
    Args:
        filename: The name of the file to write to.
        content: The text content to write.
    """
    path = WORKSPACE / filename
    path.write_text(content, encoding="utf-8")
    return f"Wrote to {filename} successfully."

model = LiteLLMModel(model_id="gemini/gemini-2.5-flash")

agent = CodeAgent(
    tools=[read_file, write_file],
    model=model,
    add_base_tools=False
)

# Write a note so the agent can read it
(WORKSPACE / "notes.txt").write_text("Madrid is a beautiful city in Spain.", encoding="utf-8")

print("Agent is reading files...")
response = agent.run("Please read 'notes.txt' and summarize what it says.")
print(f"Reply: {response}")
