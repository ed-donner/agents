import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.news_sentinel import NewsSentinel
from src.agents.accounts import Account
from src.database.database import read_latest_news_alerts

async def test_news_sentinel():
    print("Testing News Sentinel Agent")
    print("="*60)

    # Create some test holdings
    print("\n1. Setting up test accounts with holdings...")
    warren = Account.get("warren")
    if not warren.holdings:
        print("   Warren needs some holdings for testing")
        print("   Run trading floor first to generate holdings")
        return

    print(f"   Warren holdings: {list(warren.holdings.keys())}")

    # Create News Sentinel
    print("\n2. Creating News Sentinel agent...")
    news_sentinel = NewsSentinel(["warren", "george", "ray", "cathie"])

    # Get holdings map
    print("\n3. Getting holdings across all traders...")
    holdings_map = news_sentinel.get_all_holdings()
    for trader, symbols in holdings_map.items():
        print(f"   {trader.capitalize()}: {symbols}")

    # Run News Sentinel
    print("\n4. Running News Sentinel (this may take 30-60 seconds)...")
    try:
        await news_sentinel.run()
        print("   ✓ News Sentinel completed successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Check results
    print("\n5. Checking news alerts in database...")
    alerts = read_latest_news_alerts(5)
    if alerts:
        print(f"   Found {len(alerts)} alerts:")
        for alert in alerts:
            datetime, symbol, headline, sentiment, traders = alert
            print(f"   - {symbol} ({sentiment}): {headline[:60]}...")
    else:
        print("   No alerts found (this is OK if no material news)")

    print("\n✓ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_news_sentinel())
