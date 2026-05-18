import os
import asyncio
from contextlib import AsyncExitStack
from agents import Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from dotenv import load_dotenv
from security_agents import get_system_administrator, get_security_expert


load_dotenv(override=True)

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

security_server_params = MCPServerStdioParams(
    command='uv', args=['run', 'security_server.py'])


async def list_services():
    async with MCPServerStdio(params=security_server_params, client_session_timeout_seconds=60) as mcp_server:
        mcp_tools = await mcp_server.list_tools()
        print('Available tools:', [tool.name for tool in mcp_tools])
        return mcp_tools


async def call_tool(tool_name, *args):
    async with MCPServerStdio(params=security_server_params, client_session_timeout_seconds=60) as mcp_server:
        result = await mcp_server.call_tool(tool_name, *args)
        print(f'Result from {tool_name}:', result)
        return result

async def run_admin_agent(mcp_server, model_name):
    administrator_agent = await get_system_administrator(mcp_server, model_name)
    message = 'Identify potential vulnerabilities in the system and suggest mitigation strategies.'
    await Runner.run(administrator_agent, message, max_turns=5)

async def run_expert_agent(mcp_server, model_name):
    security_expert_agent = await get_security_expert(mcp_server, model_name)
    message = 'Identify potential vulnerabilities in the system and suggest mitigation strategies.'
    await Runner.run(security_expert_agent, message, max_turns=5)


async def run_with_mcp():
    async with AsyncExitStack() as stack:
        mcp_server = await stack.enter_async_context(
            MCPServerStdio(
                params=security_server_params,
                client_session_timeout_seconds=60
            )
        )
        await run_admin_agent(mcp_server, 'gpt-4o-mini')

if __name__ == '__main__':
    asyncio.run(run_with_mcp())
    # tools = asyncio.run(list_services())
    # print(asyncio.run(call_tool('search_web', {
          # 'query': 'latest cybersecurity threats', 'num_results': 5})))
