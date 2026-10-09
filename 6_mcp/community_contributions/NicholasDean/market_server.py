"""Week 6 (MCP) - the market-data server.

A second FastMCP server, separate from accounts, that just answers "what's the price?". The course
capstone uses live data (Polygon.io); this uses a fixed table so it runs with no paid data feed.
Tool: get_price; resource: market://prices. Spawned over stdio by trading_floor.py.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("market")
PRICES = {"AAPL": 200.0, "NVDA": 120.0, "MSFT": 400.0, "GOOG": 150.0, "AMZN": 180.0}


@mcp.tool()
def get_price(symbol: str) -> float:
    """Return the current share price for a symbol (0 if unknown)."""
    return PRICES.get(symbol.upper(), 0.0)


@mcp.resource("market://prices")
def prices() -> str:
    """The full price table."""
    return str(PRICES)


if __name__ == "__main__":
    mcp.run(transport="stdio")
