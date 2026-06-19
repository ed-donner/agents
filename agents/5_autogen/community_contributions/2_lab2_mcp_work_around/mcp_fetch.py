import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

async def main():
    # Connect to already-running mcp-server-fetch via stdio
    fetch_mcp_server = StdioServerParams(command="uvx", args=["mcp-server-fetch"])
    fetcher = await mcp_server_tools(fetch_mcp_server)

    # Create assistant agent
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
    agent = AssistantAgent(name="fetcher", model_client=model_client, tools=fetcher, reflect_on_tool_use=True)

    # Use the tool
    result = await agent.run(task="Review edwarddonner.com and summarize what you learn. Reply in Markdown.")
    print(result.messages[-1].content)

if __name__ == "__main__":
    asyncio.run(main())
