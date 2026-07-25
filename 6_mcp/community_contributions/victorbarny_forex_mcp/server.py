"""Combined MCP: latest rates + conversion in one process (same tools as rates_server + convert_server)."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from fx_common import convert_amount as convert_amount_impl
from fx_common import get_latest_rates as get_latest_rates_impl

mcp = FastMCP("victorbarny_forex")


@mcp.tool()
async def get_latest_rates(base: str, symbols: str) -> str:
    """Return latest exchange rates from a base currency to one or more quote currencies (Frankfurter v2).

    Args:
        base: ISO 4217 currency code for the base (e.g. USD, EUR).
        symbols: Comma-separated quote currency codes (e.g. EUR,GBP,JPY).
    """
    return await get_latest_rates_impl(base, symbols)


@mcp.tool()
async def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str,
    date: Optional[str] = None,
) -> str:
    """Convert an amount from one currency to another using the ECB-based rate (optional historical date).

    Args:
        amount: Amount to convert (must be non-negative).
        from_currency: Source ISO 4217 code.
        to_currency: Target ISO 4217 code.
        date: Optional calendar date YYYY-MM-DD for a historical rate; omit for latest.
    """
    return await convert_amount_impl(amount, from_currency, to_currency, date)


if __name__ == "__main__":
    mcp.run(transport="stdio")
