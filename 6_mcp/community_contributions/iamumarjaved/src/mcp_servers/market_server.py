import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp.server.fastmcp import FastMCP
from src.utils.market import get_share_price

mcp = FastMCP("market_server")

@mcp.tool()
async def get_share_price_tool(symbol: str) -> float:
    return get_share_price(symbol)

if __name__ == "__main__":
    mcp.run(transport='stdio')
