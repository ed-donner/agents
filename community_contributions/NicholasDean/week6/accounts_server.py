"""Week 6 (MCP) deliverable — a tiny MCP *server*.

Exposes a toy trading account over the Model Context Protocol with FastMCP: two tools (check the
balance, buy shares) and one read-only resource (a portfolio report). The client spawns this over
stdio and the agent discovers these tools automatically.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("accounts")
account = {"cash": 10_000.0, "holdings": {}}
PRICES = {"AAPL": 200.0, "NVDA": 120.0, "MSFT": 400.0}     # toy fixed prices


@mcp.tool()
def get_balance() -> float:
    """Return the account's available cash."""
    return account["cash"]


@mcp.tool()
def buy_shares(symbol: str, quantity: int) -> str:
    """Buy `quantity` shares of `symbol` if there is enough cash."""
    symbol = symbol.upper()
    cost = PRICES.get(symbol, 0) * quantity
    if cost == 0:
        return f"Unknown symbol {symbol}"
    if cost > account["cash"]:
        return f"Insufficient cash: need {cost}, have {account['cash']}"
    account["cash"] -= cost
    account["holdings"][symbol] = account["holdings"].get(symbol, 0) + quantity
    return f"Bought {quantity} {symbol} for {cost}. Cash left: {account['cash']}"


@mcp.resource("accounts://report")
def report() -> str:
    """A read-only snapshot of cash + holdings."""
    return f"Cash: {account['cash']}; Holdings: {account['holdings']}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
