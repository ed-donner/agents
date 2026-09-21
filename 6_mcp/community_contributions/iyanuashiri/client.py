"""MCP client for the Frankfurter currency server.

Connects to server.py via stdio and exposes helpers for:
  - listing available tools
  - calling any tool directly
  - three convenience wrappers matching the server's tools
"""

import asyncio
import json
from pathlib import Path

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

# Point at server.py sitting next to this file
_SERVER_PATH = str(Path(__file__).parent / "server.py")

params = StdioServerParameters(
    command="uv",
    args=["run", _SERVER_PATH],
    env=None,
)


async def list_tools():
    """Return all tools exposed by the Frankfurter MCP server."""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


async def call_tool(tool_name: str, tool_args: dict):
    """Call any tool on the server by name with the given arguments."""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result


# --- Convenience wrappers ---

async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    result = await call_tool(
        "convert_currency",
        {"amount": amount, "from_currency": from_currency, "to_currency": to_currency},
    )
    return result.content[0].text


async def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    result = await call_tool(
        "get_exchange_rate",
        {"from_currency": from_currency, "to_currency": to_currency},
    )
    return result.content[0].text


async def list_supported_currencies() -> str:
    result = await call_tool("list_supported_currencies", {})
    return result.content[0].text


# --- Quick smoke-test when run directly ---

async def _demo():
    print("=== Tools available ===")
    for tool in await list_tools():
        print(f"  {tool.name}: {tool.description}")

    print("\n=== Supported currencies ===")
    print(await list_supported_currencies())

    print("\n=== Exchange rate: USD → EUR ===")
    print(await get_exchange_rate("USD", "EUR"))

    print("\n=== Convert 100 USD to GBP ===")
    print(await convert_currency(100, "USD", "GBP"))


if __name__ == "__main__":
    asyncio.run(_demo())
