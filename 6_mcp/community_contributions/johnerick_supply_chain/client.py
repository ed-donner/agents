import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

server_params = StdioServerParameters(
    command="uv",
    args=["run", "supplychain_server.py"],
    env=None
)

async def list_tools():
    async with stdio_client(server_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools.tools

async def call_tool(tool_name: str, arguments: dict):
    async with stdio_client(server_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result

async def read_resource(uri: str):
    async with stdio_client(server_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(uri)
            return result.contents[0].text