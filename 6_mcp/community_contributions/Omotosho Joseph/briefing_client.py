import mcp as mcp_lib
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool
import json

params = StdioServerParameters(
    command="uv", args=["run", "briefing_server.py"], env=None
)


async def list_briefing_tools():
    async with stdio_client(params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_briefing_tool(tool_name, tool_args):
    async with stdio_client(params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result


async def read_todays_briefing(reporter: str) -> str:
    async with stdio_client(params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(
                f"briefings://today/{reporter}"
            )
            return result.contents[0].text


async def read_beat_resource(reporter: str) -> str:
    async with stdio_client(params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(
                f"briefings://beat/{reporter}"
            )
            return result.contents[0].text


async def get_briefing_tools_openai():
    openai_tools = []
    for tool in await list_briefing_tools():
        schema = {**tool.inputSchema, "additionalProperties": False}
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_briefing_tool(
                toolname, json.loads(args)
            ),
        )
        openai_tools.append(openai_tool)
    return openai_tools
