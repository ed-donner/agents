import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp.server.fastmcp import FastMCP
from src.database.database import write_news_alert

mcp = FastMCP("news_server")

@mcp.tool(description="Record a news alert for stocks in the database")
async def record_news_alert(symbol: str, headline: str, sentiment: str, affected_traders: str) -> str:
    """
    Record a news alert for a stock symbol in the database.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        headline: Brief news headline (1-2 sentences)
        sentiment: POSITIVE, NEGATIVE, or NEUTRAL
        affected_traders: Comma-separated list of trader names holding this stock (e.g., "warren, george")

    Returns:
        Confirmation message
    """
    try:
        write_news_alert(symbol, headline, sentiment, affected_traders)
        return f"✓ News alert recorded for {symbol} ({sentiment})"
    except Exception as e:
        return f"Error recording news alert: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
