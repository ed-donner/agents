from contextlib import AsyncExitStack
from agents import Agent, Runner, trace
from src.database.database import write_log, write_news_alert, get_connection
from src.agents.accounts import Account
from src.utils.tracers import make_trace_id
from typing import List
import json
from agents.mcp import MCPServerStdio

class NewsSentinel:
    def __init__(self, trader_names: List[str], model_name="gpt-4o-mini"):
        self.trader_names = trader_names
        self.model_name = model_name
        self.agent = None

    def get_all_holdings(self) -> dict[str, List[str]]:
        holdings_map = {}
        for trader_name in self.trader_names:
            account = Account.get(trader_name)
            symbols = list(account.holdings.keys())
            if symbols:
                holdings_map[trader_name] = symbols
        return holdings_map

    def get_unique_symbols(self, holdings_map: dict) -> List[str]:
        all_symbols = set()
        for symbols in holdings_map.values():
            all_symbols.update(symbols)
        return list(all_symbols)

    async def create_agent(self, mcp_servers) -> Agent:
        instructions = """You are the News Sentinel, monitoring breaking financial news that could impact trading positions.

Your responsibilities:
1. Analyze recent news for specific stock symbols
2. Identify material events: earnings reports, analyst ratings, regulatory issues, management changes, product launches
3. Assess sentiment: POSITIVE, NEGATIVE, or NEUTRAL
4. Record ALL material news using record_news_alert tool
5. Send push notifications for NEGATIVE news to alert traders

IMPORTANT: For EVERY material news item you find:
1. First call record_news_alert with: symbol, headline, sentiment, affected_traders
2. If sentiment is NEGATIVE, also send_push_notification to alert affected traders

Focus on:
- Breaking news (last 24 hours)
- High-impact events that could move stock prices >5%
- Verified, credible sources
- Material changes to investment thesis

Ignore:
- Minor price fluctuations (<2%)
- Speculation without substance
- Old news (>24 hours)
"""

        self.agent = Agent(
            name="NewsSentinel",
            instructions=instructions,
            model=self.model_name,
            mcp_servers=mcp_servers,
        )
        return self.agent

    async def run_agent(self, mcp_servers, holdings_map: dict):
        self.agent = await self.create_agent(mcp_servers)

        if not holdings_map:
            write_log("newssentinel", "agent", "No holdings to monitor")
            return

        symbols = self.get_unique_symbols(holdings_map)

        message = f"""Monitor these stock symbols for breaking news and significant developments:

Symbols to monitor: {', '.join(symbols)}

Current holdings by trader:
{json.dumps(holdings_map, indent=2)}

For each symbol, search for breaking news (last 24 hours) and analyze:
1. Is there material negative news (earnings miss, downgrade, scandal, regulatory issue)?
2. Is there material positive news (earnings beat, upgrade, product success)?
3. What's the sentiment and potential price impact?

IMPORTANT: For EVERY material news item you find:
1. Use record_news_alert(symbol, headline, sentiment, affected_traders) to store it
   - Example: record_news_alert("AAPL", "Apple beats Q4 earnings expectations", "POSITIVE", "warren, george")
2. If NEGATIVE news, also send_push_notification to alert traders immediately
   - Format: "⚠️ [Symbol]: [Brief headline] - affects [trader names]"

Record ALL material news (positive, negative, neutral) using record_news_alert.
Send push notifications ONLY for NEGATIVE news that requires immediate attention.

Provide a summary of your findings and the alerts you recorded.
"""

        await Runner.run(self.agent, message, max_turns=20)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            from src.utils.mcp_params import trader_mcp_server_params
            mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]

            holdings_map = self.get_all_holdings()
            await self.run_agent(mcp_servers, holdings_map)

    async def run_with_trace(self):
        trace_id = make_trace_id("newssentinel")
        with trace("news-sentinel-monitoring", trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            write_log("newssentinel", "trace", "Starting news monitoring")
            await self.run_with_trace()
            write_log("newssentinel", "trace", "Completed news monitoring")
        except Exception as e:
            error_msg = f"Error in News Sentinel: {e}"
            write_log("newssentinel", "agent", error_msg)
            print(error_msg)
