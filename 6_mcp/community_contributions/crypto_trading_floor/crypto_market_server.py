import httpx
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("crypto_market_server")

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

SYMBOL_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "ADA": "cardano", "DOT": "polkadot", "AVAX": "avalanche-2",
    "LINK": "chainlink", "MATIC": "matic-network", "ATOM": "cosmos",
    "UNI": "uniswap", "XRP": "ripple", "DOGE": "dogecoin",
    "SHIB": "shiba-inu", "LTC": "litecoin", "BNB": "binancecoin",
    "ARB": "arbitrum", "OP": "optimism", "SUI": "sui",
    "APT": "aptos", "NEAR": "near",
}

_price_cache: dict[str, tuple[float, float]] = {}
CACHE_TTL = 60


def _resolve_id(symbol: str) -> str:
    return SYMBOL_MAP.get(symbol.upper().strip(), symbol.lower().strip())


@mcp.tool()
async def lookup_crypto_price(symbol: str) -> str:
    """Get the current USD price of a cryptocurrency.

    Args:
        symbol: Ticker symbol (e.g. BTC, ETH, SOL) or CoinGecko ID
    """
    cg_id = _resolve_id(symbol)

    if cg_id in _price_cache:
        price, ts = _price_cache[cg_id]
        if time.time() - ts < CACHE_TTL:
            return f"{symbol.upper()}: ${price:,.2f}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{COINGECKO_BASE}/simple/price",
            params={"ids": cg_id, "vs_currencies": "usd"},
        )
        resp.raise_for_status()
        data = resp.json()

    if cg_id not in data:
        return f"Could not find price for '{symbol}'. Try a different symbol."

    price = data[cg_id]["usd"]
    _price_cache[cg_id] = (price, time.time())
    return f"{symbol.upper()}: ${price:,.2f}"


@mcp.tool()
async def get_top_cryptos(limit: int = 10) -> str:
    """Get top cryptocurrencies by market cap with prices and 24h change.

    Args:
        limit: Number of results (max 25, default 10)
    """
    limit = min(limit, 25)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false",
            },
        )
        resp.raise_for_status()
        coins = resp.json()

    lines = []
    for c in coins:
        sym = c["symbol"].upper()
        price = c["current_price"]
        change_24h = c.get("price_change_percentage_24h", 0) or 0
        mcap = c.get("market_cap", 0) or 0
        _price_cache[c["id"]] = (price, time.time())
        lines.append(
            f"{sym}: ${price:,.2f} (24h: {change_24h:+.1f}%) mcap: ${mcap/1e9:,.1f}B"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
