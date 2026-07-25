"""MCP server: read-only spot crypto USD pricing."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from market import get_all_crypto_prices_eod, get_crypto_price_usd
from validation import ValidationError, normalize_base_asset

mcp = FastMCP("crypto_market_server")


@mcp.tool()
async def lookup_crypto_price_usd(base_asset: str) -> str:
    """
    Last spot USD price per one unit of base_asset (e.g. BTC).
    Uses Polygon when configured; otherwise deterministic simulation prices.
    """
    try:
        base = normalize_base_asset(base_asset)
        p = get_crypto_price_usd(base)
        return json.dumps({"base_asset": base, "price_usd": p, "quote": "USD"})
    except ValidationError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


@mcp.tool()
async def batch_reference_prices_usd() -> str:
    """Cached batch of reference USD prices for supported majors (simulation / EOD cache)."""
    return json.dumps(get_all_crypto_prices_eod())


if __name__ == "__main__":
    mcp.run(transport="stdio")
