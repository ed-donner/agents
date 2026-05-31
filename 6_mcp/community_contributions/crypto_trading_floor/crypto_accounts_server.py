import json
import sqlite3
import httpx
import time
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("crypto_accounts_server")

DB = "crypto_accounts.db"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
INITIAL_BALANCE = 10_000.0
SPREAD = 0.003
CACHE_TTL = 120

SYMBOL_TO_ID = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "ADA": "cardano", "DOT": "polkadot", "AVAX": "avalanche-2",
    "LINK": "chainlink", "MATIC": "matic-network", "ATOM": "cosmos",
    "UNI": "uniswap", "XRP": "ripple", "DOGE": "dogecoin",
    "SHIB": "shiba-inu", "LTC": "litecoin", "BNB": "binancecoin",
    "ARB": "arbitrum", "OP": "optimism", "SUI": "sui",
    "APT": "aptos", "NEAR": "near",
}

_cache: dict[str, tuple[float, float]] = {}

with sqlite3.connect(DB) as conn:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)"
    )
    conn.commit()


def _write_account(name: str, data: dict):
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO accounts (name, account) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET account=excluded.account",
            (name.lower(), json.dumps(data)),
        )
        conn.commit()


def _read_account(name: str) -> dict | None:
    with sqlite3.connect(DB) as conn:
        row = conn.execute(
            "SELECT account FROM accounts WHERE name = ?", (name.lower(),)
        ).fetchone()
        return json.loads(row[0]) if row else None


def _resolve(symbol: str) -> str:
    return SYMBOL_TO_ID.get(symbol.upper().strip(), symbol.lower().strip())


def _get_price_sync(symbol: str) -> float:
    cg_id = _resolve(symbol)
    if cg_id in _cache:
        price, ts = _cache[cg_id]
        if time.time() - ts < CACHE_TTL:
            return price
    resp = httpx.get(
        f"{COINGECKO_BASE}/simple/price",
        params={"ids": cg_id, "vs_currencies": "usd"},
    )
    resp.raise_for_status()
    data = resp.json()
    if cg_id not in data:
        return 0.0
    price = data[cg_id]["usd"]
    _cache[cg_id] = (price, time.time())
    return price


def _default_account(name: str) -> dict:
    return {
        "name": name.lower(),
        "balance": INITIAL_BALANCE,
        "strategy": "",
        "holdings": {},
        "transactions": [],
        "portfolio_value_time_series": [],
    }


def _get_account(name: str) -> dict:
    acct = _read_account(name)
    if not acct:
        acct = _default_account(name)
        _write_account(name, acct)
    return acct


def _portfolio_value(acct: dict) -> float:
    total = acct["balance"]
    for sym, qty in acct["holdings"].items():
        total += _get_price_sync(sym) * qty
    return total


def _report(acct: dict) -> str:
    pv = _portfolio_value(acct)
    acct["portfolio_value_time_series"].append(
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pv)
    )
    _write_account(acct["name"], acct)
    initial_spend = sum(abs(t["quantity"]) * t["price"] for t in acct["transactions"])
    out = {**acct, "total_portfolio_value": pv, "total_profit_loss": pv - initial_spend - acct["balance"]}
    return json.dumps(out)


@mcp.tool()
async def get_balance(name: str) -> float:
    """Get the USD cash balance of a crypto trading account.

    Args:
        name: The trader's name
    """
    return _get_account(name)["balance"]


@mcp.tool()
async def get_holdings(name: str) -> dict:
    """Get current crypto holdings for a trader.

    Args:
        name: The trader's name
    """
    return _get_account(name)["holdings"]


@mcp.tool()
async def buy_crypto(name: str, symbol: str, quantity: float, rationale: str) -> str:
    """Buy a cryptocurrency. Supports fractional amounts (e.g. 0.5 BTC).

    Args:
        name: The trader's name
        symbol: Crypto ticker (e.g. BTC, ETH, SOL)
        quantity: Amount to buy (can be fractional)
        rationale: Why this trade fits the strategy
    """
    acct = _get_account(name)
    price = _get_price_sync(symbol)
    if price == 0:
        return f"Could not find price for {symbol}."
    buy_price = price * (1 + SPREAD)
    cost = buy_price * quantity
    if cost > acct["balance"]:
        return f"Insufficient funds. Need ${cost:,.2f} but have ${acct['balance']:,.2f}."
    acct["holdings"][symbol.upper()] = acct["holdings"].get(symbol.upper(), 0) + quantity
    acct["balance"] -= cost
    acct["transactions"].append({
        "symbol": symbol.upper(), "quantity": quantity, "price": buy_price,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "rationale": rationale,
    })
    _write_account(acct["name"], acct)
    return f"Bought {quantity} {symbol.upper()} at ${buy_price:,.2f}.\n" + _report(acct)


@mcp.tool()
async def sell_crypto(name: str, symbol: str, quantity: float, rationale: str) -> str:
    """Sell a cryptocurrency. Supports fractional amounts.

    Args:
        name: The trader's name
        symbol: Crypto ticker (e.g. BTC, ETH, SOL)
        quantity: Amount to sell (can be fractional)
        rationale: Why this trade fits the strategy
    """
    acct = _get_account(name)
    held = acct["holdings"].get(symbol.upper(), 0)
    if held < quantity:
        return f"Cannot sell {quantity} {symbol.upper()}. Only hold {held}."
    price = _get_price_sync(symbol)
    sell_price = price * (1 - SPREAD)
    proceeds = sell_price * quantity
    acct["holdings"][symbol.upper()] -= quantity
    if acct["holdings"][symbol.upper()] <= 0:
        del acct["holdings"][symbol.upper()]
    acct["balance"] += proceeds
    acct["transactions"].append({
        "symbol": symbol.upper(), "quantity": -quantity, "price": sell_price,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "rationale": rationale,
    })
    _write_account(acct["name"], acct)
    return f"Sold {quantity} {symbol.upper()} at ${sell_price:,.2f}.\n" + _report(acct)


@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """Update the trading strategy for a crypto trader.

    Args:
        name: The trader's name
        strategy: The new strategy description
    """
    acct = _get_account(name)
    acct["strategy"] = strategy
    _write_account(acct["name"], acct)
    return "Strategy updated."


@mcp.tool()
async def reset_account(name: str, strategy: str) -> str:
    """Reset a trader's account to starting balance with a new strategy.

    Args:
        name: The trader's name
        strategy: The investment strategy
    """
    acct = _default_account(name)
    acct["strategy"] = strategy
    _write_account(name, acct)
    return f"Account for {name} reset with ${INITIAL_BALANCE:,.0f} balance."


@mcp.resource("crypto://accounts/{name}")
async def read_account_resource(name: str) -> str:
    return _report(_get_account(name))


@mcp.resource("crypto://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    return _get_account(name)["strategy"]


if __name__ == "__main__":
    mcp.run(transport="stdio")
