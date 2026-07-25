

from __future__ import annotations

import asyncio
from pathlib import Path

from agents.mcp import MCPServerStdio


async def main() -> None:
    here = Path(__file__).resolve().parent
    rates_params = {"command": "uv", "args": ["run", str(here / "rates_server.py")]}
    convert_params = {"command": "uv", "args": ["run", str(here / "convert_server.py")]}

    async with MCPServerStdio(params=rates_params, client_session_timeout_seconds=30) as rates_mcp:
        async with MCPServerStdio(params=convert_params, client_session_timeout_seconds=30) as convert_mcp:
            r_tools = await rates_mcp.list_tools()
            c_tools = await convert_mcp.list_tools()
            print("Rates MCP tools:", [t.name for t in r_tools])
            print("Convert MCP tools:", [t.name for t in c_tools])
            print()

            rates_result = await rates_mcp.call_tool(
                "get_latest_rates",
                {"base": "USD", "symbols": "EUR,GBP"},
            )
            print("get_latest_rates(USD -> EUR,GBP):")
            print(rates_result)
            print()

            convert_result = await convert_mcp.call_tool(
                "convert_amount",
                {
                    "amount": 100.0,
                    "from_currency": "USD",
                    "to_currency": "EUR",
                },
            )
            print("convert_amount(100 USD -> EUR):")
            print(convert_result)


if __name__ == "__main__":
    asyncio.run(main())
