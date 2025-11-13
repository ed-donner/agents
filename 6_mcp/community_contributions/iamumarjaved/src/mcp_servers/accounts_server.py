import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp.server.fastmcp import FastMCP
from src.agents.accounts import Account

mcp = FastMCP("accounts_server")

@mcp.tool(description="Get the current cash balance for a trader's account")
async def get_balance(name: str) -> float:
    """
    Get the current cash balance for a trader's account.

    Args:
        name: Trader's account name (e.g., 'warren', 'george', 'ray', 'cathie')

    Returns:
        Current cash balance in dollars
    """
    try:
        return Account.get(name).balance
    except Exception as e:
        raise ValueError(f"Error getting balance for {name}: {str(e)}")

@mcp.tool(description="Get current stock holdings for a trader's account")
async def get_holdings(name: str) -> dict[str, int]:
    """
    Get current stock holdings for a trader's account.

    Args:
        name: Trader's account name

    Returns:
        Dictionary mapping stock symbols to quantities held
    """
    try:
        return Account.get(name).holdings
    except Exception as e:
        raise ValueError(f"Error getting holdings for {name}: {str(e)}")

@mcp.tool(description="Check if trader is allowed to trade based on cooldown period")
async def check_trading_cooldown(name: str) -> str:
    """
    Check if trader is allowed to trade based on cooldown period.

    Args:
        name: Trader's account name

    Returns:
        Status message indicating if trading is allowed or minutes remaining in cooldown
    """
    try:
        account = Account.get(name)
        can_trade, message = account.can_trade_now()
        if can_trade:
            return f"✓ Trading allowed. {message}"
        else:
            return f"✗ Trading not allowed. {message}"
    except Exception as e:
        return f"Error checking cooldown for {name}: {str(e)}"

@mcp.tool(description="Buy shares of a stock with detailed investment rationale")
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """
    Buy shares of a stock with detailed investment rationale.

    Args:
        name: Trader's account name
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        quantity: Number of shares to buy
        rationale: Detailed investment thesis explaining why this trade aligns with strategy

    Returns:
        Confirmation message with updated account details
    """
    try:
        return Account.get(name).buy_shares(symbol, quantity, rationale)
    except Exception as e:
        return f"Error buying shares for {name}: {str(e)}"

@mcp.tool(description="Sell shares of a stock with detailed rationale")
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """
    Sell shares of a stock with detailed rationale.

    Args:
        name: Trader's account name
        symbol: Stock ticker symbol
        quantity: Number of shares to sell
        rationale: Detailed reasoning for exiting this position

    Returns:
        Confirmation message with updated account details
    """
    try:
        return Account.get(name).sell_shares(symbol, quantity, rationale)
    except Exception as e:
        return f"Error selling shares for {name}: {str(e)}"

@mcp.tool(description="Change a trader's investment strategy")
async def change_strategy(name: str, strategy: str) -> str:
    """
    Change a trader's investment strategy.

    Args:
        name: Trader's account name
        strategy: New investment strategy description

    Returns:
        Confirmation message
    """
    try:
        return Account.get(name).change_strategy(strategy)
    except Exception as e:
        return f"Error changing strategy for {name}: {str(e)}"

@mcp.resource("accounts://accounts_server/{name}", description="Get detailed account report for a trader")
async def read_account_resource(name: str) -> str:
    """
    Get detailed account report for a trader.

    Args:
        name: Trader's account name

    Returns:
        JSON report with balance, holdings, transactions, and portfolio value history
    """
    try:
        account = Account.get(name.lower())
        return account.report()
    except Exception as e:
        return f"Error reading account for {name}: {str(e)}"

@mcp.resource("accounts://strategy/{name}", description="Get current investment strategy for a trader")
async def read_strategy_resource(name: str) -> str:
    """
    Get current investment strategy for a trader.

    Args:
        name: Trader's account name

    Returns:
        Text description of trader's investment strategy
    """
    try:
        account = Account.get(name.lower())
        return account.get_strategy()
    except Exception as e:
        return f"Error reading strategy for {name}: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
