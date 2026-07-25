import asyncio
import sys
from agents.mcp import MCPServerStdio
from mcp import StdioServerParameters


params = StdioServerParameters(
    command="uv", args=["run", "traveller_server.py"], env=None
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# params = {"command": "python", "args": ["traveller.py"]}
params = {"command": "uv", "args": ["run", "traveller_server.py"]}


async def start():
    async with MCPServerStdio(
        params=params, client_session_timeout_seconds=30
    ) as server:
        print(server)
        tools = await server.list_tools()
        print(tools)


asyncio.run(start())
