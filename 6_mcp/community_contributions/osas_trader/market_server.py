from mcp.server.fastmcp import FastMCP
from market import get_share_price

mcp = FastMCP("market_server")


@mcp.tool()
async def lookup_share_price(symbol: str) -> float:
    """Get the current price of a stock symbol.

    Args:
        symbol: The ticker symbol of the stock
    """
    return get_share_price(symbol)


if __name__ == "__main__":
    mcp.run(transport="stdio")
