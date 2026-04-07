import mcp
import os
import shutil
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

node_path = shutil.which("node") or "/usr/local/bin/node"
node_dir = os.path.dirname(node_path)
env = os.environ.copy()
env["PATH"] = f"{node_dir}:{env.get('PATH', '')}"
uv_command = shutil.which("uv") or "/opt/homebrew/bin/uv"

params = StdioServerParameters(command=uv_command, args=["run", "travel_server.py"], env=env)


async def list_travel_tools():
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def read_travel_profile(name: str) -> str:
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"travel://profile/{name}")
            return result.contents[0].text


async def read_travel_preferences(name: str) -> str:
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"travel://preferences/{name}")
            return result.contents[0].text


async def read_travel_itinerary(name: str) -> str:
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"travel://itinerary/{name}")
            return result.contents[0].text
