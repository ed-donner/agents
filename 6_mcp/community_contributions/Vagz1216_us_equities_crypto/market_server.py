from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path

ROOT_6_MCP = Path(__file__).resolve().parents[2]
if str(ROOT_6_MCP) not in sys.path:
    sys.path.append(str(ROOT_6_MCP))

from market import get_share_price

mcp = FastMCP("market_server_us_equities_crypto")


@mcp.tool()
async def lookup_share_price(symbol: str) -> float:
    """Return current price for equities ticker or supported crypto symbol."""
    return get_share_price(symbol)


if __name__ == "__main__":
    mcp.run(transport="stdio")
