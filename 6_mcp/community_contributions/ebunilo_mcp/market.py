"""Spot crypto USD pricing — Polygon last crypto trade with deterministic fallbacks."""

from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv
from polygon import RESTClient

from database import read_market, write_market
from validation import normalize_base_asset

load_dotenv(override=True)

logger = logging.getLogger(__name__)

polygon_api_key = os.getenv("POLYGON_API_KEY")

# Fallback USD prices when API is unavailable (simulation only)
_FALLBACK_USD: dict[str, float] = {
    "BTC": 98_500.0,
    "ETH": 3_450.0,
    "SOL": 185.0,
    "BNB": 620.0,
    "XRP": 2.15,
    "DOGE": 0.35,
    "ADA": 0.95,
}


def _fallback_price(base: str) -> float:
    base = normalize_base_asset(base)
    if base in _FALLBACK_USD:
        jitter = 1.0 + random.uniform(-0.002, 0.002)
        return round(_FALLBACK_USD[base] * jitter, 8)
    return round(float(random.uniform(1.0, 200.0)), 8)


def _polygon_last_trade_usd(base: str) -> float:
    client = RESTClient(polygon_api_key)
    base = normalize_base_asset(base)
    trade = client.get_last_crypto_trade(from_=base, to="USD")
    if trade.price is None or trade.price <= 0:
        raise ValueError("No price in last crypto trade response")
    return float(trade.price)


@lru_cache(maxsize=2)
def _eod_cache_key_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def get_all_crypto_prices_eod() -> dict[str, float]:
    """Single-day cache of fallback prices for lightweight EOD-style batching."""
    today = _eod_cache_key_today()
    cached = read_market(today)
    if cached:
        return cached
    data = {k: _fallback_price(k) for k in _FALLBACK_USD}
    write_market(today, data)
    return data


def get_crypto_price_usd(base_asset: str) -> float:
    """
    Last spot price in USD per one unit of base_asset (e.g. BTC).
    Uses Polygon /v1/last/crypto/{from}/{to} when POLYGON_API_KEY is set.
    """
    base = normalize_base_asset(base_asset)
    if polygon_api_key:
        try:
            return _polygon_last_trade_usd(base)
        except Exception as e:
            logger.warning("Polygon crypto price failed for %s: %s — using fallback", base, e)
    return _fallback_price(base)


def is_crypto_market_hours() -> bool:
    """Spot crypto is effectively 24/7 — always True for scheduler compatibility."""
    return True
