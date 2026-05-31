from mcp.server.fastmcp import FastMCP

from accounts_crypto import Account

mcp = FastMCP("accounts_server_crypto")


@mcp.tool()
async def get_balance(name: str) -> float:
    """Cash balance (USD notional) for the account."""
    return Account.get(name).balance


@mcp.tool()
async def get_holdings(name: str) -> dict[str, float]:
    """Holdings: symbol -> spot units (fractional sizes supported)."""
    return Account.get(name).holdings


@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: float, rationale: str) -> float:
    """Buy spot crypto units (e.g. BTC, ETH). Price from Binance public API."""
    return Account.get(name).buy_shares(symbol, quantity, rationale)


@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: float, rationale: str) -> float:
    """Sell spot crypto units."""
    return Account.get(name).sell_shares(symbol, quantity, rationale)


@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """Update investment strategy text for future runs."""
    return Account.get(name).change_strategy(strategy)


@mcp.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    account = Account.get(name.lower())
    return account.report()


@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    account = Account.get(name.lower())
    return account.get_strategy()


if __name__ == "__main__":
    mcp.run(transport="stdio")
