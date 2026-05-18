from agents.mcp import MCPServerStdio
import asyncio
from date_client import call_date_tool, list_date_tools


async def main():
    tools = await list_date_tools()
    print("Available tools:", tools)

    date_result = await call_date_tool("get_current_date")
    print("Current date (local timezone):", date_result.structuredContent['result'])

    timezone_result = await call_date_tool("get_current_date_with_timezone", {"timezone": "US/Eastern"})
    print("Current date (US/Eastern):", timezone_result.structuredContent['result'])

if __name__ == "__main__":
    asyncio.run(main())