"""Week 6 (MCP) - the accounts server.

A FastMCP server that holds one trading account and records trades. It deliberately knows nothing
about prices - the trader gets those from the separate market server and passes the price in. Tools:
get_balance, buy_shares; resource: accounts://report. Spawned over stdio by trading_floor.py.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("accounts")
account = {"cash": 10_000.0, "holdings": {}}


@mcp.tool()
def get_balance() -> float:
    """Return the account's available cash."""
    return account["cash"]


@mcp.tool()
def buy_shares(symbol: str, quantity: int, price: float) -> str:
    """Buy `quantity` shares of `symbol` at `price` (look the price up from the market server first)."""
    symbol = symbol.upper()
    cost = price * quantity
    if cost > account["cash"]:
        return f"Insufficient cash: need {cost:.2f}, have {account['cash']:.2f}"
    account["cash"] -= cost
    account["holdings"][symbol] = account["holdings"].get(symbol, 0) + quantity
    return f"Bought {quantity} {symbol} @ {price}. Cash left: {account['cash']:.2f}"


@mcp.resource("accounts://report")
def report() -> str:
    """A read-only snapshot of cash + holdings."""
    return f"Cash: {account['cash']:.2f}; Holdings: {account['holdings']}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
