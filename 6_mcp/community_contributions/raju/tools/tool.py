import sys
from pathlib import Path
import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool
import json

#Use the same Python interpreter and an absolute path to the server script to avoid errors
#venv should be in activated before run
_SERVER_PATH = str((Path(__file__).parent / "date_server.py").resolve())
params = StdioServerParameters(command=sys.executable, args=["-u", _SERVER_PATH], env=None)

async def _list_tools():
    try:
        async with stdio_client(params) as streams:
            async with mcp.ClientSession(*streams) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return tools_result.tools
    except OSError as e:
        raise RuntimeError(f"Failed to spawn server script {_SERVER_PATH!r}: {e}") from e


async def _call_tool(name, args):
    try:
        async with stdio_client(params) as streams:
            async with mcp.ClientSession(*streams) as session:
                await session.initialize()
                result = await session.call_tool(name, args)
                return result
    except OSError as e:
        raise RuntimeError(f"Failed to spawn server script {_SERVER_PATH!r}: {e}") from e


async def get_openai_tools():
    tools=[]
    for tool in await _list_tools():
        schema = {**tool.inputSchema, "additionalProperties":False}
        openai_tool = FunctionTool(
                name=tool.name,
                description=tool.description,
                params_json_schema=schema,
                on_invoke_tool = lambda ctx,args,toolname=tool.name: _call_tool(toolname, json.loads(args))
        )
        tools.append(openai_tool)
    return tools
