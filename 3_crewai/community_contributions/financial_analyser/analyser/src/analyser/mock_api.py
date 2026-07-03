import random
from datetime import datetime, timedelta


# ---------- MOCK STOCK DATA (AlphaVantage-like response) ----------
def get_mock_stock_data(symbol: str):
    """Simulates historical price data for a stock symbol."""
    base_price = 150 + random.uniform(-10, 10)
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    mock_data = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "open": round(base_price + random.uniform(-5, 5), 2),
            "close": round(base_price + random.uniform(-5, 5), 2),
            "volume": random.randint(500000, 2000000)
        }
        for d in dates
    ]
    return {"symbol": symbol, "prices": mock_data}


# ---------- MOCK CRYPTO DATA (Coinbase-like response) ----------
def get_mock_crypto_data(symbol: str):
    """Simulates simple crypto market data."""
    return {
        "symbol": symbol,
        "price_usd": round(random.uniform(25000, 45000), 2),
        "24h_change": round(random.uniform(-5, 5), 2),
        "volume_24h": random.randint(1000000, 10000000),
        "timestamp": datetime.now().isoformat(),
    }


# ---------- MOCK NEWS SENTIMENT (NewsAPI-like response) ----------
def get_mock_news_sentiment(query: str):
    """Simulates a list of recent news headlines and their sentiment."""
    headlines = [
        f"{query} hits new quarterly earnings record",
        f"Analysts divided on {query} market outlook",
        f"Investors express optimism as {query} shows resilience",
        f"{query} stock experiences short-term volatility",
        f"Experts warn of overvaluation in {query} shares",
    ]

    sentiments = ["positive", "neutral", "negative"]
    news_items = [
        {
            "headline": headline,
            "sentiment": random.choice(sentiments),
            "source": random.choice(["Bloomberg", "Reuters", "CNBC", "FT"]),
            "confidence": round(random.uniform(0.6, 0.95), 2),
        }
        for headline in headlines
    ]

    return {
        "query": query,
        "articles": news_items,
        "overall_sentiment": random.choice(["positive", "neutral", "negative"]),
    }
