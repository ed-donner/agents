import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# IMPORTANT: variable name MUST be PARAMS (uppercase)
PARAMS = StdioServerParameters(
    command="uv",
    args=["run", "emoji_server.py"],
    env=None
)

# -------------------- List Tools --------------------
async def list_emoji_tools():
    async with stdio_client(PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools

# -------------------- Call Tool --------------------
async def call_emoji_tool(tool_name: str, arguments: dict = None):
    arguments = arguments or {}
    async with stdio_client(PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                name=tool_name,
                arguments=arguments
            )
            return result
