"""
crypto_traders.py
Extension to the trading simulator — adds crypto-focused agents.

New agents:
    Luna    — momentum crypto trader (rides trends)
    Satoshi — Bitcoin maximalist / crypto value investor
    Nova    — cross-asset trader (stocks + crypto ETFs)

Usage:
    from crypto_traders import create_crypto_traders
    traders = create_crypto_traders()
    await asyncio.gather(*[t.run() for t in traders])
"""

import os
import json
import asyncio
from datetime import datetime
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from accounts_client import read_accounts_resource, read_strategy_resource
from accounts import Account
from tracers import make_trace_id
from mcp_params import trader_mcp_server_params, researcher_mcp_server_params

load_dotenv(override=True)

MAX_TURNS = 30

# Free CoinGecko MCP — no API key needed for basic endpoints
COINGECKO_MCP = {
    "command": "npx",
    "args":    ["-y", "@coingecko/coingecko-mcp"],
}

# ── CRYPTO RESEARCHER MCP PARAMS ─────────────────────────────
def crypto_researcher_mcp_params(name: str) -> list:
    os.makedirs("memory", exist_ok=True)    # ← add this line
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        COINGECKO_MCP,
        {
            "command": "npx",
            "args":    ["-y", "mcp-memory-libsql"],
            "env":     {"LIBSQL_URL": f"file:./memory/{name.lower()}.db"},
        },
    ]


# ── CRYPTO PERSONAS ───────────────────────────────────────────
CRYPTO_TRADERS = [
    {
        "name":     "Luna",
        "lastname": "Momentum",
        "model":    "gpt-4o-mini",
        "strategy": (
            "You are a crypto momentum trader. You ride trends — buy assets "
            "that are going up, sell when momentum reverses. "
            "Focus on altcoins with high trading volume and strong price action. "
            "Use CoinGecko data to spot trending coins. "
            "Use crypto ETFs (BITO, IBIT, FBTC) when direct crypto isn't available. "
            "Cut losses quickly — never hold a losing position more than 2 runs."
        ),
    },
    {
        "name":     "Satoshi",
        "lastname": "Value",
        "model":    "gpt-4o-mini",
        "strategy": (
            "You are a Bitcoin-focused value investor. "
            "You believe Bitcoin is digital gold and hold it long-term via ETFs like IBIT or FBTC. "
            "You also take measured positions in Ethereum ETFs (ETHA) when valuations are attractive. "
            "You are patient — you buy dips and hold. "
            "Only sell if fundamentals deteriorate significantly. "
            "Avoid speculative altcoins — stick to proven assets."
        ),
    },
    {
        "name":     "Nova",
        "lastname": "CrossAsset",
        "model":    "gpt-4o-mini",
        "strategy": (
            "You are a cross-asset trader who balances traditional equities with crypto exposure. "
            "Maintain 60% in tech stocks (NVDA, MSFT, AMZN, META) and 40% in crypto ETFs (IBIT, ETHA, BITO). "
            "Rebalance when allocations drift more than 10% from targets. "
            "Use macro news to tilt — risk-on means more crypto, risk-off means more equities. "
            "Research both stock and crypto markets before making decisions."
        ),
    },
]


# ── TEMPLATES ─────────────────────────────────────────────────

def crypto_researcher_instructions() -> str:
    return f"""You are a crypto and financial researcher with access to CoinGecko data.
You search the web for financial and crypto news, find trading opportunities, and summarize findings.
Use CoinGecko tools to get current crypto prices, trending coins, and market data.
Use web search for macro news, regulatory developments, and sentiment.
Make multiple searches for a comprehensive view. Store findings in your knowledge graph.
If rate limited on search, use the fetch tool to read specific pages directly.
The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def crypto_trader_instructions(name: str, strategy: str) -> str:
    return f"""You are {name}, a trader managing a portfolio.
Your account is under your name: {name}.

Your strategy:
{strategy}

You have access to:
- A Researcher tool to search the web and get crypto/stock data
- Account tools to buy and sell shares and crypto ETFs
- Market data tools to check prices
- Memory tools to store and recall research

Since you cannot buy crypto directly, use crypto ETFs:
    Bitcoin  → IBIT, FBTC, BITO
    Ethereum → ETHA
    Broad crypto → BITQ, WGMI

Important: always check your current balance before trading.
Execute trades autonomously — do not ask for confirmation.
After trading, send a push notification summarising your actions.
Respond with a 2-3 sentence portfolio appraisal.
"""


def crypto_trade_message(name: str, strategy: str, account: str) -> str:
    return f"""Research the crypto and stock markets, then execute trades aligned with your strategy.

Your strategy: {strategy}
Your account:  {account}
Current time:  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Steps:
1. Use the Researcher tool to get current crypto prices and news
2. Check your balance and current holdings
3. Identify opportunities matching your strategy
4. Execute trades — buy or sell as appropriate
5. Send a push notification with a trade summary
6. Reply with a 2-3 sentence portfolio appraisal

Your account name is {name}.
"""


def crypto_rebalance_message(name: str, strategy: str, account: str) -> str:
    return f"""Review your existing portfolio and rebalance if needed.

Your strategy: {strategy}
Your account:  {account}
Current time:  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Steps:
1. Use the Researcher tool to check news affecting your current holdings
2. Review current prices vs your entry prices
3. Rebalance according to your strategy targets
4. Execute any necessary trades
5. Send a push notification with a rebalance summary
6. Reply with a 2-3 sentence portfolio appraisal

Your account name is {name}.
"""


# ── CRYPTO TRADER CLASS ───────────────────────────────────────

class CryptoTrader:
    """
    Crypto-aware trader agent.
    Alternates between trade and rebalance modes each run.
    Uses CoinGecko MCP for real crypto market data.
    """

    def __init__(self, name: str, lastname: str, model_name: str, strategy: str):
        self.name       = name
        self.lastname   = lastname
        self.model_name = model_name
        self.strategy   = strategy
        self.do_trade   = True
        self.agent      = None

    def get_model(self):
        """Route model name to correct provider client."""
        if "/" in self.model_name:
            openrouter_client = AsyncOpenAI(
                base_url = "https://openrouter.ai/api/v1",
                api_key  = os.getenv("OPENROUTER_API_KEY")
            )
            return OpenAIChatCompletionsModel(
                model         = self.model_name,
                openai_client = openrouter_client
            )
        return self.model_name  # plain string → OpenAI native

    async def get_researcher_tool(self, researcher_mcp_servers) -> Tool:
        researcher = Agent(
            name         = f"{self.name}-Researcher",
            instructions = crypto_researcher_instructions(),
            model        = self.get_model(),
            mcp_servers  = researcher_mcp_servers,
        )
        return researcher.as_tool(
            tool_name        = "Researcher",
            tool_description = (
                "Researches crypto prices via CoinGecko, web news via search, "
                "and stores findings in memory. Describe what you need researched."
            ),
        )

    async def get_account_report(self) -> str:
        account      = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        researcher_tool = await self.get_researcher_tool(researcher_mcp_servers)

        self.agent = Agent(
            name         = self.name,
            instructions = crypto_trader_instructions(self.name, self.strategy),
            model        = self.get_model(),
            tools        = [researcher_tool],
            mcp_servers  = trader_mcp_servers,
        )

        account = await self.get_account_report()
        message = (
            crypto_trade_message(self.name, self.strategy, account)
            if self.do_trade
            else crypto_rebalance_message(self.name, self.strategy, account)
        )

        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in crypto_researcher_mcp_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        mode     = "trading" if self.do_trade else "rebalancing"
        trace_id = make_trace_id(self.name.lower())
        with trace(f"{self.name}-{mode}", trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running crypto trader {self.name}: {e}")
        self.do_trade = not self.do_trade


# ── FACTORY ───────────────────────────────────────────────────

def create_crypto_traders() -> list[CryptoTrader]:
    """Create and initialise all crypto trader agents."""
    traders = []
    for config in CRYPTO_TRADERS:
        # Initialise account with strategy if new
        account = Account.get(config["name"])
        if not account.strategy:
            account.reset(config["strategy"])
            print(f"Initialised {config['name']} with strategy: {config['lastname']}")

        traders.append(CryptoTrader(
            name       = config["name"],
            lastname   = config["lastname"],
            model_name = config["model"],
            strategy   = config["strategy"],
        ))
    return traders


# ── STANDALONE RUN ────────────────────────────────────────────

async def run_once():
    """Run all crypto traders once — useful for testing."""
    traders = create_crypto_traders()
    await asyncio.gather(*[trader.run() for trader in traders])
    print("All crypto traders completed one run.")


if __name__ == "__main__":
    asyncio.run(run_once())