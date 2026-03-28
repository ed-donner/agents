"""
Technical Analysis MCP Server

Exposes Polygon.io technical indicators (SMA, EMA, RSI, MACD) and historical
price aggregates as MCP tools so that an AI agent can perform technical analysis.
"""

from mcp.server.fastmcp import FastMCP
from polygon import RESTClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import json

load_dotenv(override=True)

polygon_api_key = os.getenv("POLYGON_API_KEY")
client = RESTClient(polygon_api_key)

mcp = FastMCP("ta_server")


# helper

def _fmt(val):
    """Return a JSON-safe representation of Polygon model objects."""
    if hasattr(val, "__dict__"):
        return {k: v for k, v in val.__dict__.items() if not k.startswith("_")}
    return val


# tools


@mcp.tool()
async def get_price_history(symbol: str, days: int = 30, timespan: str = "day") -> str:
    """Get historical OHLCV price bars for a stock.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
        days: How many calendar days of history (default 30)
        timespan: Bar size – 'minute', 'hour', 'day', 'week', 'month' (default 'day')
    """
    try:
        end = datetime.now().date()
        start = end - timedelta(days=days)
        aggs = list(client.list_aggs(symbol, 1, timespan, start.isoformat(), end.isoformat(), adjusted=True, limit=5000))
        bars = []
        for a in aggs:
            bars.append({
                "date": datetime.fromtimestamp(a.timestamp / 1000).strftime("%Y-%m-%d"),
                "open": a.open,
                "high": a.high,
                "low": a.low,
                "close": a.close,
                "volume": a.volume,
            })
        return json.dumps(bars[-60:])   # cap at 60 bars
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


@mcp.tool()
async def get_sma(symbol: str, window: int = 20, timespan: str = "day", limit: int = 10) -> str:
    """Get Simple Moving Average (SMA) values for a stock.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
        window: SMA window period (default 20)
        timespan: 'day', 'week', 'month' etc. (default 'day')
        limit: Number of data points to return (default 10)
    """
    try:
        result = client.get_sma(symbol, timespan=timespan, window=window, adjusted=True, order="desc", limit=limit)
        values = [_fmt(v) for v in (result.values or [])]
        return json.dumps(values)
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


@mcp.tool()
async def get_ema(symbol: str, window: int = 20, timespan: str = "day", limit: int = 10) -> str:
    """Get Exponential Moving Average (EMA) values for a stock.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
        window: EMA window period (default 20)
        timespan: 'day', 'week', 'month' etc. (default 'day')
        limit: Number of data points to return (default 10)
    """
    try:
        result = client.get_ema(symbol, timespan=timespan, window=window, adjusted=True, order="desc", limit=limit)
        values = [_fmt(v) for v in (result.values or [])]
        return json.dumps(values)
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


@mcp.tool()
async def get_rsi(symbol: str, window: int = 14, timespan: str = "day", limit: int = 10) -> str:
    """Get Relative Strength Index (RSI) values for a stock.

    RSI > 70 is typically considered overbought; RSI < 30 is oversold.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
        window: RSI window (default 14)
        timespan: 'day', 'week', 'month' etc. (default 'day')
        limit: Number of data points to return (default 10)
    """
    try:
        result = client.get_rsi(symbol, timespan=timespan, window=window, adjusted=True, order="desc", limit=limit)
        values = [_fmt(v) for v in (result.values or [])]
        return json.dumps(values)
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


@mcp.tool()
async def get_macd(
    symbol: str,
    short_window: int = 12,
    long_window: int = 26,
    signal_window: int = 9,
    timespan: str = "day",
    limit: int = 10,
) -> str:
    """Get MACD (Moving Average Convergence Divergence) values for a stock.

    Returns MACD line, signal line, and histogram for each data point.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
        short_window: Fast EMA window (default 12)
        long_window: Slow EMA window (default 26)
        signal_window: Signal line EMA window (default 9)
        timespan: 'day', 'week', 'month' etc. (default 'day')
        limit: Number of data points to return (default 10)
    """
    try:
        result = client.get_macd(
            symbol,
            timespan=timespan,
            short_window=short_window,
            long_window=long_window,
            signal_window=signal_window,
            adjusted=True,
            order="desc",
            limit=limit,
        )
        values = [_fmt(v) for v in (result.values or [])]
        return json.dumps(values)
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


@mcp.tool()
async def get_previous_close(symbol: str) -> str:
    """Get the previous trading day's OHLCV bar for a stock.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
    """
    try:
        aggs = client.get_previous_close_agg(symbol, adjusted=True)
        bars = [_fmt(a) for a in aggs]
        return json.dumps(bars)
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


@mcp.tool()
async def get_ticker_news(symbol: str, limit: int = 5) -> str:
    """Get the latest news articles for a stock ticker from Polygon.

    Args:
        symbol: Ticker symbol (e.g. AAPL)
        limit: Max articles to return (default 5)
    """
    try:
        articles = list(client.list_ticker_news(symbol, limit=limit))
        results = []
        for a in articles:
            results.append({
                "title": getattr(a, "title", ""),
                "author": getattr(a, "author", ""),
                "published_utc": getattr(a, "published_utc", ""),
                "article_url": getattr(a, "article_url", ""),
                "description": getattr(a, "description", ""),
            })
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e), "symbol": symbol})


if __name__ == "__main__":
    mcp.run(transport="stdio")
