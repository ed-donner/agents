import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool
import json

def _logs_params() -> StdioServerParameters:
    return StdioServerParameters(command="uv", args=["run", "logs_server.py"], env=None)

def _network_params() -> StdioServerParameters:
    return StdioServerParameters(command="uv", args=["run", "network_server.py"], env=None)



async def _list_tools(params: StdioServerParameters):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return (await session.list_tools()).tools


async def _call_tool(params: StdioServerParameters, tool_name: str, tool_args: dict):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return await session.call_tool(tool_name, tool_args)



async def list_logs_tools():
    return await _list_tools(_logs_params())


async def call_logs_tool(tool_name: str, tool_args: dict):
    return await _call_tool(_logs_params(), tool_name, tool_args)


async def list_network_tools():
    return await _list_tools(_network_params())


async def call_network_tool(tool_name: str, tool_args: dict):
    return await _call_tool(_network_params(), tool_name, tool_args)



def _to_function_tools(tools, call_fn) -> list[FunctionTool]:
    result = []
    for tool in tools:
        schema = {**tool.inputSchema, "additionalProperties": False}
        result.append(FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            on_invoke_tool=lambda ctx, args, tn=tool.name: call_fn(tn, json.loads(args)),
        ))
    return result


async def get_logs_tools_openai() -> list[FunctionTool]:
    return _to_function_tools(await list_logs_tools(), call_logs_tool)


async def get_network_tools_openai() -> list[FunctionTool]:
    return _to_function_tools(await list_network_tools(), call_network_tool)
