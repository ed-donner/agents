from mcp.server.fastmcp import FastMCP
import pandas as pd
import random

mcp = FastMCP("MarketDataServer")

@mcp.tool()
def get_stock_price(ticker: str) -> str:
    """Fetches the current price and volume for a given stock ticker."""
    price = round(random.uniform(150, 200), 2)
    volume = random.randint(1000000, 5000000)
    
    return f"Ticker: {ticker}, Price: ${price}, Volume: {volume}"

@mcp.tool()
def get_market_sentiment(ticker: str) -> str:
    """Retrieves recent news sentiment for a ticker."""
    sentiments = ["Bullish", "Bearish", "Neutral"]
    return f"Current sentiment for {ticker} is {random.choice(sentiments)}."

if __name__ == "__main__":
    mcp.run()