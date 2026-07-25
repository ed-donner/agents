from __future__ import annotations

import asyncio
from pathlib import Path

from agents.mcp import MCPServerStdio


async def main() -> None:
    here = Path(__file__).resolve().parent
    params = {"command": "uv", "args": ["run", str(here / "server.py")]}

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        tools = await server.list_tools()
        print("Available tools:")
        for t in tools:
            print(f"  - {t.name}")
        print()

        result = await server.call_tool(
            "convert_amount",
            {
                "amount": 100.0,
                "from_currency": "USD",
                "to_currency": "EUR",
            },
        )
        print("convert_amount(100 USD -> EUR):")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
