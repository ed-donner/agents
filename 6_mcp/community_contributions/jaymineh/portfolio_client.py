"""
portfolio_client.py — MCP Client for portfolio_notes_server

Connects to portfolio_notes_server.py via stdio and exposes its tools in two formats:
  - Native OpenAI format  (dict list for direct chat.completions calls — no Agents SDK)
  - Agents SDK format     (FunctionTool objects for use with Agent)

Also provides read_notes_resource() to pull prior research as an MCP resource.
"""
import json
import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from agents import FunctionTool

params = StdioServerParameters(
    command="uv",
    args=["run", "community_contributions/jaymineh/portfolio_notes_server.py"],
    env=None,
)


async def list_notes_tools():
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return (await session.list_tools()).tools


async def call_notes_tool(tool_name: str, tool_args: dict) -> str:
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result.content[0].text


async def read_notes_resource(symbol: str) -> str:
    """Read all research notes for a symbol via the MCP resource interface."""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"notes://{symbol.upper()}")
            return result.contents[0].text


async def get_notes_tools_openai_format() -> list[dict]:
    """Return tools as plain dicts for the native openai.AsyncOpenAI client."""
    tools = []
    for tool in await list_notes_tools():
        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {**tool.inputSchema, "additionalProperties": False},
                "strict": True,
            },
        })
    return tools


async def get_notes_tools_agents_sdk() -> list[FunctionTool]:
    """Return tools as FunctionTool objects for the OpenAI Agents SDK."""
    sdk_tools = []
    for tool in await list_notes_tools():
        sdk_tools.append(
            FunctionTool(
                name=tool.name,
                description=tool.description,
                params_json_schema={**tool.inputSchema, "additionalProperties": False},
                on_invoke_tool=lambda ctx, args, name=tool.name: call_notes_tool(
                    name, json.loads(args)
                ),
            )
        )
    return sdk_tools
