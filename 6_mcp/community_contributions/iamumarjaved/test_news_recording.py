"""
Test News Sentinel alert recording functionality
"""
import asyncio
from contextlib import AsyncExitStack
from agents.mcp import MCPServerStdio
from agents import Agent, Runner
from src.database.database import read_latest_news_alerts

async def test_news_recording():
    print("Testing News Sentinel Alert Recording")
    print("="*60)

    async with AsyncExitStack() as stack:
        # Start MCP servers
        from src.utils.mcp_params import trader_mcp_server_params
        mcp_servers = [
            await stack.enter_async_context(
                MCPServerStdio(params, client_session_timeout_seconds=60)
            )
            for params in trader_mcp_server_params
        ]

        # Create test agent
        agent = Agent(
            name="TestNewsAgent",
            instructions="""You are testing the news alert recording system.

Your task:
1. Record 3 test news alerts using the record_news_alert tool
2. Use different sentiments: POSITIVE, NEGATIVE, NEUTRAL
3. Use realistic stock symbols and headlines

Example calls:
- record_news_alert("AAPL", "Apple beats Q4 earnings by 15%", "POSITIVE", "warren, ray")
- record_news_alert("TSLA", "Tesla recalls 2M vehicles over safety issue", "NEGATIVE", "cathie")
- record_news_alert("NVDA", "NVIDIA announces new datacenter chip", "POSITIVE", "ray, george")

After recording, confirm all 3 alerts were saved.""",
            model="gpt-4o-mini",
            mcp_servers=mcp_servers,
        )

        print("\n1. Running agent to record test alerts...")
        await Runner.run(agent, "Record 3 different news alerts using record_news_alert tool", max_turns=10)

        print("\n2. Checking database for recorded alerts...")
        alerts = read_latest_news_alerts(10)

        if alerts:
            print(f"\n✓ Found {len(alerts)} alert(s) in database:")
            for alert in alerts:
                datetime, symbol, headline, sentiment, traders = alert
                sentiment_emoji = {
                    "NEGATIVE": "🔴",
                    "POSITIVE": "🟢",
                    "NEUTRAL": "🟡"
                }.get(sentiment, "⚪")
                print(f"  {sentiment_emoji} {symbol}: {headline} (affects: {traders})")
        else:
            print("\n✗ No alerts found in database")

        print("\n" + "="*60)
        print("✓ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_news_recording())
