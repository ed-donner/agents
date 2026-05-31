from mcp.server.fastmcp import FastMCP
from .crypto_market import get_crypto_price, is_crypto

mcp = FastMCP("crypto_market_server")


@mcp.tool()
async def lookup_crypto_price(symbol: str) -> float:
    """
    Get the current price of a cryptocurrency.

    Args:
        symbol: Crypto symbol such as BTC, ETH, or SOL
    """
    symbol = symbol.upper()

    if not is_crypto(symbol):
        raise ValueError(f"{symbol} is not a supported crypto asset")

    return get_crypto_price(symbol)


if __name__ == "__main__":
    mcp.run(transport="stdio")