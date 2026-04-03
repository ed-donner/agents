"""
market.py

This file contains the market data layer and the market MCP server
  - Market data layer    (Polygon.io integration, EOD/paid/realtime tiers)
  - Market MCP server    (FastMCP — exposes share price lookup as MCP tool)
  - Push notification    (Pushover — exposes push as MCP tool)

"""

import os
import random
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv
from polygon import RESTClient
from pydantic import BaseModel, Field
import requests
from mcp.server.fastmcp import FastMCP
# (accounts.py imports market.py for get_share_price; market.py imports accounts.py for DB)

load_dotenv(override=True)

# Setup the market data using Polygon.io

polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"


def is_market_open() -> bool:
    client = RESTClient(polygon_api_key)
    return client.get_market_status().market == "open"


def get_all_share_prices_polygon_eod() -> dict[str, float]:
    """Fetch previous day's closing prices for all tickers via Polygon."""
    client = RESTClient(polygon_api_key)
    probe = client.get_previous_close_agg("SPY")[0]
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
    results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
    return {result.ticker: result.close for result in results}


@lru_cache(maxsize=2)
def get_market_for_prior_date(today: str) -> dict[str, float]:
    from accounts import read_market, write_market
    data = read_market(today)
    if not data:
        data = get_all_share_prices_polygon_eod()
        write_market(today, data)
    return data


def get_share_price_polygon_eod(symbol: str) -> float:
    today = datetime.now().date().strftime("%Y-%m-%d")
    return get_market_for_prior_date(today).get(symbol, 0.0)


def get_share_price_polygon_min(symbol: str) -> float:
    client = RESTClient(polygon_api_key)
    result = client.get_snapshot_ticker("stocks", symbol)
    return result.min.close or result.prev_day.close


def get_share_price_polygon(symbol: str) -> float:
    return get_share_price_polygon_min(symbol) if is_paid_polygon else get_share_price_polygon_eod(symbol)


def get_share_price(symbol: str) -> float:
    if polygon_api_key:
        try:
            return get_share_price_polygon(symbol)
        except Exception as e:
            print(f"Polygon API error for {symbol}: {e}. Using random price.")
    return float(random.randint(1, 100))


# Setup the push notifications using Pushover
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def send_push(message: str) -> str:
    """Send a Pushover push notification directly (non-MCP use)."""
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    try:
        requests.post(PUSHOVER_URL, data=payload)
        print(f"Push sent: {message}")
        return "Push notification sent"
    except Exception as e:
        print(f"Push failed: {e}")
        return f"Push failed: {e}"


# MCP Server  (market data + push notifications combined)
# Entry point: uv run market.py
mcp_server = FastMCP("market_server")


@mcp_server.tool()
async def lookup_share_price(symbol: str) -> float:
    """Get the current price of the given stock symbol.

    Args:
        symbol: the ticker symbol of the stock
    """
    return get_share_price(symbol)


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push (under 200 chars)")


@mcp_server.tool()
def push(args: PushModelArgs) -> str:
    """Send a push notification with this brief message."""
    return send_push(args.message)


if __name__ == "__main__":
    mcp_server.run(transport="stdio")
