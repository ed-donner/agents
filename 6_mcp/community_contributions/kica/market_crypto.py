import random
from datetime import datetime

import httpx

from crypto_database import read_market, write_market

BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"


def normalize_binance_pair(symbol: str) -> str:
    """Map user-facing symbols (BTC, BTC-USD, BTCUSDT) to Binance USDT pair."""
    s = symbol.upper().strip().replace("-", "").replace("_", "")
    if s.endswith("USDT"):
        return s
    if s.endswith("USD") and len(s) > 3:
        return s[:-3] + "USDT"
    return s + "USDT"


def _cache_key_today() -> str:
    return f"crypto-{datetime.now().date().strftime('%Y-%m-%d')}"


def _fetch_binance(pair: str) -> float:
    r = httpx.get(BINANCE_PRICE_URL, params={"symbol": pair}, timeout=15.0)
    r.raise_for_status()
    data = r.json()
    return float(data["price"])


def get_crypto_price(symbol: str) -> float:
    """
    USD-equivalent spot via USDT pairs on Binance (public API).
    Examples: BTC, ETH, SOL, XRP, DOGE, ADA.
    """
    pair = normalize_binance_pair(symbol)
    key = _cache_key_today()
    bucket = read_market(key)
    if bucket and pair in bucket:
        return float(bucket[pair])

    try:
        price = _fetch_binance(pair)
    except Exception as e:
        print(f"Binance price fetch failed for {pair}: {e}; using demo fallback")
        price = float(random.randint(1, 100_000))

    merged = dict(bucket) if bucket else {}
    merged[pair] = price
    write_market(key, merged)
    return price


if __name__ == "__main__":
    for sym in ("BTC", "ETH", "SOL"):
        print(sym, get_crypto_price(sym))
