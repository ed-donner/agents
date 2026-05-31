from mcp.server.fastmcp import FastMCP
from tools import AccountManager, Account, Holdings, Transaction, PolygonClient, serper_search as _serper_search, generate_pdf_from_text as _generate_pdf_from_text
from typing import List
from datetime import datetime


mcp = FastMCP("trading_mcp")

manager = AccountManager()
polygon = PolygonClient()


@mcp.tool()
async def get_account(account_id: str) -> Account:
    """Get the account details for the given account ID."""
    return manager.get_account(account_id)

@mcp.tool()
async def create_account(account_name: str, account_type: str) -> Account:
    """Create a new account with the given name and type."""
    return manager.create_account(account_name, account_type)

@mcp.tool()
async def deposit(account_id: str, amount: float) -> Account:
    """Deposit the given amount into the given account."""
    return manager.deposit(account_id, amount)

@mcp.tool()
async def withdraw(account_id: str, amount: float) -> Account:
    """Withdraw the given amount from the given account."""
    return manager.withdraw(account_id, amount)

@mcp.tool()
async def buy_shares(account_id: str, symbol: str, units: int, rationale: str = "") -> Account:
    """Buy the given number of shares at the live market price for the given account."""
    return manager.buy_shares(account_id, symbol, units, rationale)

@mcp.tool()
async def sell_shares(account_id: str, symbol: str, units: int, rationale: str = "") -> Account:
    """Sell the given number of shares at the live market price for the given account."""
    return manager.sell_shares(account_id, symbol, units, rationale)

@mcp.tool()
async def get_account_balance(account_id: str) -> float:
    """Get the balance of the given account."""
    return manager.get_account_balance(account_id)

@mcp.tool()
async def get_account_holdings(account_id: str) -> List[Holdings]:
    """Get the holdings of the given account."""
    return manager.get_account_holdings(account_id)

@mcp.tool()
async def change_strategy(account_id: str, strategy: str) -> Account:
    """Change the strategy of the given account."""
    return manager.change_strategy(account_id, strategy)

@mcp.tool()
async def get_account_strategy(account_id: str) -> str:
    """Get the strategy of the given account."""
    return manager.get_account_strategy(account_id)

@mcp.tool()
async def calculate_portfolio_value(account_id: str) -> float:
    """Calculate the portfolio value of the given account using live prices."""
    return manager.calculate_portfolio_value(account_id)

@mcp.tool()
async def calculate_profit_loss(account_id: str) -> float:
    """Calculate the total unrealized profit/loss of the given account using live prices."""
    return manager.calculate_profit_loss(account_id)

@mcp.tool()
async def get_profit_loss(account_id: str) -> dict[str, float]:
    """Get the profit/loss broken down per symbol for the given account using live prices."""
    return manager.get_profit_loss(account_id)

@mcp.tool()
async def list_transactions(account_id: str) -> List[Transaction]:
    """List all transactions for the given account."""
    return manager.list_transactions(account_id)

@mcp.tool()
async def report(account_id: str) -> str:
    """Get a full report of the given account using live prices."""
    return manager.report(account_id)

@mcp.tool()
async def send_email(subject: str, html_body: str) -> dict:
    """Send an email to the user using Mailgun."""
    return manager.send_email(subject, html_body)

@mcp.tool()
async def write_log(name: str, type: str, message: str) -> None:
    """Write a log entry for the given account name."""
    return manager.write_log(name, type, message)

@mcp.tool()
async def read_log(name: str, last_n: int = 10) -> list:
    """Read the most recent log entries for the given account name."""
    return manager.read_log(name, last_n)

@mcp.tool()
async def write_memory(account_id: str, messages: list) -> None:
    """Write the given messages to the memory of the given account."""
    return manager.write_memory(account_id, messages)

@mcp.tool()
async def read_memory(account_id: str) -> list:
    """Read the memory of the given account."""
    return manager.read_memory(account_id)

@mcp.tool()
async def lookup_share_price(symbol: str) -> float:
    """Get the current price of the given stock symbol.

    Args:
        symbol: the ticker symbol of the stock e.g. AAPL, MSFT, TSLA
    """
    return polygon.get_share_price(symbol)

@mcp.tool()
async def is_market_open() -> bool:
    """Check if the US stock market is currently open."""
    return polygon.is_market_open()

@mcp.tool()
async def get_current_date() -> str:
    """Get the current date in the format YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

@mcp.tool()
async def serper_search(query: str) -> list:
    """Search the web using Serper API."""
    return _serper_search(query)

@mcp.tool()
async def generate_pdf_from_text(content: str, filename: str, is_markdown: bool = True) -> str:
    """Generate a PDF from the given text."""
    return _generate_pdf_from_text(content, filename, is_markdown)

@mcp.tool()
async def get_portfolio_value_display(account_id: str) -> tuple[float, float]:
    """Get the portfolio value display for the given account."""
    return manager.get_portfolio_value_display(account_id)

@mcp.tool()
async def get_share_prices(symbols: list[str]) -> dict[str, float]:
    """Get current prices for multiple stock symbols in one call.
    
    Args:
        symbols: list of ticker symbols e.g. ["AAPL", "MSFT", "TSLA"]
    """
    return polygon.get_share_prices(symbols)

if __name__ == "__main__":
    mcp.run(transport='stdio')