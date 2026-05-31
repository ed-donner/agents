"""MCP server: fake USD + spot crypto execution and account queries."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from accounts import Account
from database import DB, read_log
from market import polygon_api_key
from validation import ValidationError

load_dotenv(override=True)

mcp = FastMCP("crypto_accounts_server")

SUPPORTED_BASE_ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA"]


def _err(e: Exception) -> str:
    return f"Error: {type(e).__name__}: {e}"


@mcp.tool()
async def get_usd_balance(name: str) -> str:
    """Return fake USD (stablecoin simulation) cash balance for the named trader."""
    try:
        bal = Account.get(name).usd_balance
        return json.dumps({"usd_balance": bal, "currency": "USD_SIM"})
    except Exception as e:
        return _err(e)


@mcp.tool()
async def get_crypto_holdings(name: str) -> str:
    """Return spot crypto holdings as JSON: base asset -> quantity in base units."""
    try:
        h = Account.get(name).get_holdings()
        return json.dumps(h)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def buy_crypto(name: str, base_asset: str, quantity_base: float, rationale: str) -> str:
    """
    Buy spot crypto with fake USD. `base_asset` is the base symbol (e.g. BTC, ETH).
    `quantity_base` is the amount in base units (fractional allowed).
    """
    try:
        return Account.get(name).buy_crypto(base_asset, quantity_base, rationale)
    except (ValidationError, ValueError) as e:
        return _err(e)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def sell_crypto(name: str, base_asset: str, quantity_base: float, rationale: str) -> str:
    """
    Sell spot crypto for fake USD. `quantity_base` is base units to sell.
    """
    try:
        return Account.get(name).sell_crypto(base_asset, quantity_base, rationale)
    except (ValidationError, ValueError) as e:
        return _err(e)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """Update the trader's written strategy for future runs."""
    try:
        return Account.get(name).change_strategy(strategy)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def get_supported_crypto_assets() -> str:
    """List base assets supported by this simulator (pricing + validation)."""
    return json.dumps(
        {
            "assets": SUPPORTED_BASE_ASSETS,
            "note": "Spot simulation only — not real custody or exchange execution.",
        }
    )


@mcp.tool()
async def get_recent_transactions(name: str, limit: int = 20) -> str:
    """Return the most recent spot crypto transactions (JSON array)."""
    try:
        limit = max(1, min(int(limit), 200))
        txs = Account.get(name).list_transactions()[-limit:]
        return json.dumps(txs)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def get_system_health() -> str:
    """Runtime health: database path, Polygon key presence, Python version."""
    return json.dumps(
        {
            "status": "ok",
            "database": DB,
            "polygon_configured": bool(polygon_api_key),
            "python": sys.version.split()[0],
            "utc_time": datetime.now(timezone.utc).isoformat(),
        }
    )


@mcp.tool()
async def get_audit_log(name: str, last_n: int = 25) -> str:
    """Recent account/audit log lines for a trader (from SQLite)."""
    try:
        last_n = max(1, min(int(last_n), 500))
        rows = list(read_log(name, last_n=last_n))
        return json.dumps([{"datetime": r[0], "type": r[1], "message": r[2]} for r in rows])
    except Exception as e:
        return _err(e)


@mcp.resource("crypto-accounts://accounts/{name}")
async def read_account_resource(name: str) -> str:
    return Account.get(name.lower()).report()


@mcp.resource("crypto-accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    return Account.get(name.lower()).get_strategy()


if __name__ == "__main__":
    mcp.run(transport="stdio")
