"""
MCP server: multi-venue execution intelligence (paper-trading / simulation only).
Uses public APIs where possible (CoinGecko, Frankfurter). Optional Polygon if POLYGON_API_KEY is set.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

mcp = FastMCP("multi_exchange_intel")

# Static venue metadata for routing education (not live brokerage data)
VENUES: dict[str, dict[str, Any]] = {
    "US_EQUITY_CENTRAL": {
        "asset_classes": ["equity"],
        "typical_latency_ms": 50,
        "fee_bps_est": 1.0,
        "notes": "US listed; use Polygon or broker API for quotes when configured.",
    },
    "NSE_DELAYED": {
        "asset_classes": ["equity"],
        "typical_latency_ms": 800,
        "fee_bps_est": 8.0,
        "notes": "Nigeria-listed; often delayed retail feeds; watch currency and settlement.",
    },
    "CRYPTO_SPOT_AGG": {
        "asset_classes": ["crypto"],
        "typical_latency_ms": 120,
        "fee_bps_est": 10.0,
        "notes": "Global crypto; 24/7; volatility and venue fragmentation matter.",
    },
    "FX_SPOT_RETAIL": {
        "asset_classes": ["fx"],
        "typical_latency_ms": 200,
        "fee_bps_est": 3.0,
        "notes": "FX via bank/broker spread; ECB reference rates are indicative only.",
    },
}


@mcp.tool()
async def list_venues() -> str:
    """List supported logical venues with latency/fee estimates for smart routing."""
    return json.dumps(VENUES, indent=2)


@mcp.tool()
async def get_fx_rate(from_currency: str, to_currency: str) -> str:
    """Spot FX using Frankfurter (ECB). Example: from_currency=USD, to_currency=NGN."""
    url = f"https://api.frankfurter.app/latest?from={from_currency.upper()}&to={to_currency.upper()}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)


@mcp.tool()
async def get_crypto_quote(coin_id: str) -> str:
    """CoinGecko simple price (no API key, rate-limited). coin_id examples: bitcoin, ethereum."""
    cid = coin_id.strip().lower()
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, headers={"Accept": "application/json"})
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)


@mcp.tool()
async def get_equity_hint(symbol: str) -> str:
    """If POLYGON_API_KEY is set, fetch last close via Polygon; else return simulation hint."""
    key = os.getenv("POLYGON_API_KEY")
    sym = symbol.strip().upper()
    if not key:
        return json.dumps(
            {
                "symbol": sym,
                "mode": "simulated",
                "message": "Set POLYGON_API_KEY for live US equity snapshot; using placeholder.",
                "placeholder_price": 100.0,
            },
            indent=2,
        )
    try:
        from polygon import RESTClient

        client = RESTClient(key)
        snap = client.get_previous_close_agg(sym)
        row = snap[0]
        return json.dumps(
            {
                "symbol": sym,
                "mode": "polygon_prior_close",
                "close": float(row.close),
                "timestamp_ms": int(row.timestamp),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"symbol": sym, "error": str(e)}, indent=2)


def _score_venue(
    venue_id: str,
    asset_class: str,
    notional: float,
    max_slippage_bps: float,
) -> dict[str, Any]:
    meta = VENUES.get(venue_id)
    if not meta or asset_class not in meta["asset_classes"]:
        return {"venue": venue_id, "score": 0.0, "reason": "asset class mismatch"}
    slip_penalty = max(0.0, meta["fee_bps_est"] - max_slippage_bps * 0.1)
    latency_penalty = meta["typical_latency_ms"] / 500.0
    size_penalty = 0.0 if notional < 50_000 else 2.0
    score = max(0.0, 100.0 - slip_penalty - latency_penalty - size_penalty)
    return {
        "venue": venue_id,
        "score": round(score, 2),
        "fee_bps_est": meta["fee_bps_est"],
        "latency_ms": meta["typical_latency_ms"],
        "notes": meta["notes"],
    }


@mcp.tool()
async def compare_venues(
    symbol: str,
    asset_class: str,
    notional_usd: float,
    side: str,
    max_slippage_bps: float = 25.0,
) -> str:
    """Rank venues for a hypothetical order. asset_class: equity | crypto | fx. side: buy | sell."""
    ac = asset_class.strip().lower()
    ranked = []
    for vid in VENUES:
        ranked.append(_score_venue(vid, ac, float(notional_usd), float(max_slippage_bps)))
    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
    return json.dumps(
        {
            "symbol": symbol.strip().upper(),
            "side": side.strip().lower(),
            "notional_usd": notional_usd,
            "ranked": ranked,
        },
        indent=2,
    )


def _symbol_asset_class(sym: str) -> tuple[str, str | None]:
    s = sym.strip().upper()
    if s in {"BTC", "BITCOIN"}:
        return "crypto", "bitcoin"
    if s in {"ETH", "ETHEREUM"}:
        return "crypto", "ethereum"
    if s.endswith("-USD") or s.endswith("USDT"):
        return "crypto", "bitcoin"
    return "equity", None


@mcp.tool()
async def smart_route(
    goal: str,
    symbols_json: str,
    risk_profile: str,
    max_slippage_bps: float = 25.0,
) -> str:
    """Produce a structured multi-venue routing suggestion from goal + symbol list (JSON array string)."""
    try:
        symbols = json.loads(symbols_json)
    except json.JSONDecodeError:
        symbols = [symbols_json]
    if not isinstance(symbols, list):
        symbols = [str(symbols)]
    out: dict[str, Any] = {
        "goal": goal,
        "risk_profile": risk_profile,
        "max_slippage_bps": max_slippage_bps,
        "suggestions": [],
    }
    for sym in symbols:
        s = str(sym).strip().upper()
        ac, coin_id = _symbol_asset_class(s)
        row: dict[str, Any] = {"symbol": s, "asset_class": ac}
        if ac == "crypto" and coin_id:
            cq = await get_crypto_quote(coin_id)
            row["quote_hint"] = json.loads(cq)
        ranked = json.loads(
            await compare_venues(s, ac, notional_usd=10_000, side="buy", max_slippage_bps=max_slippage_bps)
        )
        row["venue_ranking"] = ranked.get("ranked", [])
        out["suggestions"].append(row)
    return json.dumps(out, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
