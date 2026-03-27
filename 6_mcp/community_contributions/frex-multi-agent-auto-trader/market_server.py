"""FastMCP server for end-of-day market data (free Polygon tier)."""
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from market import get_share_price as fetch_share_price

mcp = FastMCP("market_server")


class SharePriceArgs(BaseModel):
    symbol: str = Field(description="Stock ticker symbol (e.g. AAPL)")


@mcp.tool()
def get_share_price(args: SharePriceArgs) -> float:
    """End-of-day share price as of the prior close (free Polygon tier)."""
    return fetch_share_price(args.symbol)


if __name__ == "__main__":
    mcp.run(transport="stdio")
