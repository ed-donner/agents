"""
Test the MCP server over stdio (spawns server as subprocess).

Run: uv run python demo_client.py
"""

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

ROOT = Path(__file__).resolve().parent


def _first_text_from_tool_result(result: CallToolResult) -> str:
    """Prefer the first text block; avoid assuming content[0] is TextContent."""
    if not result.content:
        return str(result)
    for block in result.content:
        if isinstance(block, TextContent):
            return block.text
    return repr(result.content[0])


async def main() -> None:
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server.py"],
        cwd=str(ROOT),
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to curiosity_break MCP (stdio).\n")
            listed = await session.list_tools()
            print("Tools:")
            for t in listed.tools:
                print(f"  • {t.name}")
            print()

            for name, args in [
                ("xkcd_latest", {}),
                ("random_advice", {}),
                ("xkcd_by_number", {"comic_number": 303}),
            ]:
                result = await session.call_tool(name, arguments=args)
                text = _first_text_from_tool_result(result)
                print(f"--- {name} ---")
                print(text)
                print()


if __name__ == "__main__":
    asyncio.run(main())
