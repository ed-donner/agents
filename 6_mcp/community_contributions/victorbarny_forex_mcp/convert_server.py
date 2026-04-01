

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from fx_common import convert_amount as convert_amount_impl

mcp = FastMCP("victorbarny_forex_convert")


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
