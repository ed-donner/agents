from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import os
import random
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from polygon import RESTClient

ROOT_6_MCP = Path(__file__).resolve().parents[2]
if str(ROOT_6_MCP) not in sys.path:
    sys.path.append(str(ROOT_6_MCP))

from database import read_market, write_market

load_dotenv(override=True)

polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"

CRYPTO_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
}


def _normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    aliases = {
        "BTCUSD": "BTC",
        "ETHUSD": "ETH",
        "SOLUSD": "SOL",
        "XBT": "BTC",
    }
    return aliases.get(value, value)


def is_crypto_symbol(symbol: str) -> bool:
    return _normalize_symbol(symbol) in CRYPTO_ID_MAP


def is_market_open() -> bool:
    # Keep class behavior: only equities schedule is market-hours gated.
    if not polygon_api_key:
        return True
    client = RESTClient(polygon_api_key)
    market_status = client.get_market_status()
    return market_status.market == "open"


def get_all_share_prices_polygon_eod() -> dict[str, float]:
    client = RESTClient(polygon_api_key)
    probe = client.get_previous_close_agg("SPY")[0]
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
    results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
    return {result.ticker: result.close for result in results}


@lru_cache(maxsize=2)
def get_market_for_prior_date(today: str):
    market_data = read_market(today)
    if not market_data:
        market_data = get_all_share_prices_polygon_eod()
        write_market(today, market_data)
    return market_data


def get_share_price_polygon_eod(symbol: str) -> float:
    today = datetime.now().date().strftime("%Y-%m-%d")
    market_data = get_market_for_prior_date(today)
    return market_data.get(symbol, 0.0)


def get_share_price_polygon_min(symbol: str) -> float:
    client = RESTClient(polygon_api_key)
    result = client.get_snapshot_ticker("stocks", symbol)
    return result.min.close or result.prev_day.close


def get_share_price_polygon(symbol: str) -> float:
    if is_paid_polygon:
        return get_share_price_polygon_min(symbol)
    return get_share_price_polygon_eod(symbol)


def get_crypto_price(symbol: str) -> float:
    normalized = _normalize_symbol(symbol)
    coin_id = CRYPTO_ID_MAP.get(normalized)
    if not coin_id:
        return 0.0
    url = "https://api.coingecko.com/api/v3/simple/price"
    response = requests.get(url, params={"ids": coin_id, "vs_currencies": "usd"}, timeout=10)
    response.raise_for_status()
    return float(response.json().get(coin_id, {}).get("usd", 0.0))


def get_share_price(symbol: str) -> float:
    normalized = _normalize_symbol(symbol)
    if is_crypto_symbol(normalized):
        try:
            return get_crypto_price(normalized)
        except Exception as e:
            print(f"Crypto API unavailable ({e}); using random fallback")
            return float(random.randint(10, 200))

    if polygon_api_key:
        try:
            return get_share_price_polygon(normalized)
        except Exception as e:
            print(f"Polygon API unavailable ({e}); using random fallback")
    return float(random.randint(1, 100))
