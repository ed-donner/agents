import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async def main():
    server_path = Path(__file__).parent / "server.py"

    mcp_params = {
        "command": "python",
        "args": [str(server_path)]
    }

    mcp_server = MCPServerStdio(mcp_params)
    await mcp_server.connect()

    instructions = """
    You are a helpful assistant.

    You can:
    - save notes using tools
    - retrieve notes using tools

    Always use the tools when asked to store or retrieve information.
    """

    agent = Agent(
        name="NotesAgent",
        instructions=instructions,
        mcp_servers=[mcp_server],
        model="gpt-4o-mini"
    )

    print("Assistant ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        result = await Runner.run(agent, user_input)
        print("\nAssistant:", result.final_output, "\n")

if __name__ == "__main__":
    asyncio.run(main())
  