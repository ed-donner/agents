"""
List available tools from a remote MCP server using the OpenAI Agents SDK.

Requires:
    pip install openai-agents

Usage:
    python3 list_mcp_tools_openai.py
"""

import asyncio
from agents.mcp import MCPServerStreamableHttp

MCP_SERVER_URL = "https://mcp.trymalcolm.com/mcp-ab2a870c-468a-418a-b695-09a30559a22a/V28"


async def main():
    async with MCPServerStreamableHttp(
        name="malcolm",
        params={"url": MCP_SERVER_URL},
    ) as server:
        tools = await server.list_tools()

        print(f"Server: {server.name}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())