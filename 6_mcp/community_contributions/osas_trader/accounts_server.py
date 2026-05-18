from mcp.server.fastmcp import FastMCP
from accounts import Account

mcp = FastMCP("accounts_server")


@mcp.tool()
async def get_balance(name: str) -> float:
    """Get the cash balance of the given account.

    Args:
        name: The account holder's name
    """
    return Account.get(name).balance


@mcp.tool()
async def get_holdings(name: str) -> dict:
    """Get all positions. Positive quantity = long; negative quantity = short.

    Args:
        name: The account holder's name
    """
    return Account.get(name).get_holdings()


@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Buy shares of a stock to open or extend a long position.
    Also use this to cover (close) a short position.

    Args:
        name: The account holder's name
        symbol: Stock ticker symbol
        quantity: Number of shares to buy (positive integer)
        rationale: Why this trade fits the strategy
    """
    return Account.get(name).buy_shares(symbol, quantity, rationale)


@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Sell shares you currently hold (long position only).
    To open a short position on a stock you don't own, use short_sell instead.

    Args:
        name: The account holder's name
        symbol: Stock ticker symbol
        quantity: Number of shares to sell
        rationale: Why this trade fits the strategy
    """
    return Account.get(name).sell_shares(symbol, quantity, rationale)


@mcp.tool()
async def short_sell(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Open or extend a SHORT position — sell shares you don't own.

    Profit when the stock price falls; loss when it rises (losses can be large).
    Requires 150% of the position value as margin in the account.
    Use cover_short to close the position.

    Args:
        name: The account holder's name
        symbol: Stock ticker symbol
        quantity: Number of shares to short (positive integer)
        rationale: Why you expect this stock to decline
    """
    return Account.get(name).short_sell(symbol, quantity, rationale)


@mcp.tool()
async def cover_short(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Close (or reduce) a short position by buying back the borrowed shares.

    Args:
        name: The account holder's name
        symbol: Stock ticker symbol
        quantity: Number of shares to buy back
        rationale: Why you are closing the short now
    """
    return Account.get(name).cover_short(symbol, quantity, rationale)


@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """Update your investment strategy description.

    Args:
        name: The account holder's name
        strategy: The new strategy text
    """
    return Account.get(name).change_strategy(strategy)


@mcp.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    return Account.get(name.lower()).report()


@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    return Account.get(name.lower()).get_strategy()


if __name__ == "__main__":
    mcp.run(transport="stdio")
