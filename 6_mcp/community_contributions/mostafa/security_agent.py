import asyncio
import json

from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from mcp import StdioServerParameters


security_params = MCPServerStdioParams(command='uv', args=['run', 'security_server.py'])

async def list_services():
    async with MCPServerStdio(params=security_params, client_session_timeout_seconds=60) as mcp_server:
        mcp_tools = await mcp_server.list_tools()
        print('Available tools:', [tool.name for tool in mcp_tools])
        return mcp_tools


async def call_tool(tool_name, *args):
    async with MCPServerStdio(params=security_params, client_session_timeout_seconds=60) as mcp_server:
        result = await mcp_server.call_tool(tool_name, *args)
        print(f'Result from {tool_name}:', result)
        return result
    
if __name__ == '__main__':
    tools = asyncio.run(list_services())
    print(asyncio.run(call_tool('search_web', {'query': 'latest cybersecurity threats', 'num_results': 5})))
    
