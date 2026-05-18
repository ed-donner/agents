from mcp.server.fastmcp import FastMCP

from market_crypto import get_crypto_price

mcp = FastMCP("crypto_market_server")


@mcp.tool()
async def lookup_crypto_price(symbol: str) -> float:
    """Current USDT spot price (Binance public API, no key).

    Symbols: BTC, ETH, SOL, XRP, ADA, DOGE, or BTCUSDT-style pairs.

    Args:
        symbol: Base asset or pair, e.g. BTC, ETH, BTCUSDT.
    """
    return get_crypto_price(symbol)


if __name__ == "__main__":
    mcp.run(transport="stdio")
