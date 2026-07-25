

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from fx_common import get_latest_rates as get_latest_rates_impl

mcp = FastMCP("victorbarny_forex_rates")


@mcp.tool()
async def get_latest_rates(base: str, symbols: str) -> str:
    """Return latest exchange rates from a base currency to one or more quote currencies (Frankfurter v2).

    Args:
        base: ISO 4217 currency code for the base (e.g. USD, EUR).
        symbols: Comma-separated quote currency codes (e.g. EUR,GBP,JPY).
    """
    return await get_latest_rates_impl(base, symbols)


if __name__ == "__main__":
    mcp.run(transport="stdio")
