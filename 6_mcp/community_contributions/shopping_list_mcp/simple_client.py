"""
simple_client.py - Test the Shopping List MCP Server

This connects to the MCP server and tests all tools directly.
No LLM involved - just direct tool calls.

Run with: uv run simple_client.py
"""
import asyncio  
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    """Connect to the shopping list server and test all tools."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("🛒 Shopping List MCP Server - Test Client")
            print("=" * 50)
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # Test add_item tool
            print("🎁 Adding items to the shopping list...")
            result = await session.call_tool("add_item", arguments={"name": "Milk", "quantity": 2, "category": "Dairy", "price": 4.99})
            print(f"  Result: {result.content[0].text}")
            print()

            # Test get_list tool
            print("📋 Getting current shopping list...")
            result = await session.call_tool("get_list", arguments={})
            print(f"  Result: {result.content[0].text}")
            print()

            # Test set_budget tool  
            print("💰 Setting budget to $25...")
            result = await session.call_tool("set_budget", arguments={"amount": 25.0})
            print(f"  Result: {result.content[0].text}")
            print()

            # Test get_budget_status tool
            print("📊 Checking budget status...")
            result = await session.call_tool("get_budget_status", arguments={})
            print(f"  Result: {result.content[0].text}")
            print()

            # Test remove_item tool
            print("🗑️ Removing item...")
            result = await session.call_tool("remove_item", arguments={"name": "Milk"})
            print(f"  Result: {result.content[0].text}")
            print()

            # Test clear_list tool
            print("🧹 Clearing shopping list...")
            result = await session.call_tool("clear_list", arguments={})
            print(f"  Result: {result.content[0].text}")
            print()
            
            print("📋 Final shopping list:")
            result = await session.call_tool("get_list", arguments={})
            print(result.content[0].text)
            print()

            print("✅ All tests completed!")

if __name__ == "__main__":
     asyncio.run(main())