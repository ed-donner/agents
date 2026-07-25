from dotenv import load_dotenv
import os
import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents.mcp import MCPServerStdio
from agents import FunctionTool, Runner, Agent
import json
from IPython.display import display, Markdown
import asyncio

load_dotenv(override=True)

# Playwright Tools
playwright_params = {'command': 'npx', 'args': ['-y', '@playwright/mcp@latest']}

# async def list_playwright_tools():
#     async with MCPServerStdio(params=playwright_params, client_session_timeout_seconds=60) as browser_server:
#         playwright_tools = await browser_server.list_tools()
#     return playwright_tools

# File Tools
news_path = '/home/adri/projects/agents/6_mcp/adriana_exercise_day2/news'

files_params = {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-filesystem', news_path]}

# async def list_file_tools():
#     async with MCPServerStdio(params=files_params, client_session_timeout_seconds=60) as news_server:
#         file_tools = await news_server.list_tools()
#     return file_tools

# Date Tools
date_params = StdioServerParameters(command='uv', args=['run', 'date_server.py'], env=None)

async def list_date_tools():
    async with stdio_client(date_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools
    
async def call_date_tool(tool_name, tool_args):
    async with stdio_client(date_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result
        
async def get_current_date() -> str:
    result = await call_date_tool('get_current_date', {})
    return result

date_tool = FunctionTool(
    name="get_current_date",
    description="Get today's date (YYYY-MM-DD) from the date MCP server.",
    params_json_schema={"type": "object", "properties": {}, "required": []},
    on_invoke_tool=lambda ctx, args: call_date_tool('get_current_date', {})
)


# Main Client        
instructions = """
You are a news reporter. You are given a topic and you will use the tools provided to you and fetch the news for the topic
from the current date. 
For each of the 5 items you MUST provide a real URL and a serperate headline.
If you can not find a URL, search again.
In the markdwon each bullet must be in this format: 
1. Headline
    URL
2. Headline
    URL 
    ....
Provide the results with the current date, the headlines and the urls of the articles you found in a markdwon file in the news folder.
""" 
topic = 'AI'
request = f'get me the news for {topic}'
model = 'gpt-4.1-mini'


async def main():
    async with MCPServerStdio(params=playwright_params, client_session_timeout_seconds=60) as mcp_server, \
        MCPServerStdio(params=files_params, client_session_timeout_seconds=60) as news_server:
        agent = Agent(
            name = 'news_agent',
            instructions = instructions,
            model = model,
            tools = [date_tool],
            mcp_servers = [mcp_server, news_server]
        )
        result = await Runner.run(agent, request)
        print(result.final_output)
        display(Markdown(result.final_output))
        
        
if __name__ == '__main__':
    asyncio.run(main())