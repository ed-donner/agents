import logging
import asyncio
import os
import sys
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# 1. Globally suppress all logging from all libraries
logging.basicConfig(level=logging.CRITICAL) 
logging.getLogger().setLevel(logging.CRITICAL)

# 2. Specifically target the 'agents' and 'mcp' loggers
for logger_name in ["agents", "mcp", "mcp.client.stdio", "mcp.server"]:
    l = logging.getLogger(logger_name)
    l.setLevel(logging.CRITICAL)
    l.propagate = False

load_dotenv(override=True)

async def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "date_server.py")
    params = {"command": "uv", "args": ["run", server_path]}

    async with MCPServerStdio(params=params) as server:
        await server.list_tools()

        agent = Agent(
            name="date_assistant", 
            instructions="You are a helpful assistant.", 
            model="gpt-4o-mini", 
            mcp_servers=[server]
        )
        
        result = await Runner.run(agent, "What is the current date?")
        
        # 3. Clean output
        print(f"Result: {result.final_output}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass