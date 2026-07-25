from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
import os
from tools.tool import get_openai_tools
import asyncio

load_dotenv(override=True)

base_url = "https://openrouter.ai/api/v1"
key = os.getenv("OPENROUTER_API_KEY")

provider = AsyncOpenAI(api_key=key, base_url=base_url)
model = OpenAIChatCompletionsModel(openai_client=provider, model="openrouter/free")

async def using_openAI_builtin():
    '''MCP client using OpenAI MCP support'''
    params={"command":"uv", "args":["run","tools/date_server.py"]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        agent = Agent(model=model, name="tool_user", instructions="You are tool using agent", mcp_servers=[server])
        output = await Runner.run(agent, input="Get me today date")
        return output.final_output

async def using_manual_MCP_client():
    '''manually retreived tool using MCP client'''
    tools = await get_openai_tools()
    agent = Agent(name="tool_user", model=model, instructions="You are tool using agent", tools = tools)
    output = await Runner.run(agent, input="Get me today date")
    return output.final_output

async def run_by_option(method):
    result = await (using_manual_MCP_client() if method=="2" else using_openAI_builtin())
    print(result)


if __name__ == "__main__":
    print("1. call openAI MCP client [default]")
    print("2. call manual MCP client")
    method = input("choose option: ")
    asyncio.run(run_by_option(method))
