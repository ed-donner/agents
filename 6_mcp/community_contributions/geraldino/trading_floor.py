"""
trading_floor.py

This file contains the trading floor and the risk manager
  - MCP server params    (which MCP servers each agent uses)
  - Prompt templates     (system prompts and messages for all agents)
  - Tracers              (logging every agent span to the DB)
  - Risk Manager         (LLM agent that monitors loss thresholds, emails + pushes alerts)
  - Trader class         (individual AI trader agent with researcher sub-agent)  

Environment variables (.env):
  OPENROUTER_API_KEY            — required (all models routed via OpenRouter)
  OPENAI_API_KEY                — fallback for plain model names
  BRAVE_API_KEY                 — for researcher web search
  POLYGON_API_KEY               — for market data (optional, random prices used if absent)
  POLYGON_PLAN                  — free | paid | realtime
  PUSHOVER_USER                 — Pushover user key
  PUSHOVER_TOKEN                — Pushover app token
  SENDGRID_API_KEY              — for risk manager email reports
  RISK_EMAIL_FROM               — verified SendGrid sender address
  RISK_EMAIL_TO                 — your email to receive risk reports
  RUN_EVERY_N_MINUTES           — trading cycle interval (default: 60)
  RUN_EVEN_WHEN_MARKET_IS_CLOSED — true | false (default: false)
  RISK_THRESHOLD_PCT            — loss % that triggers Risk Manager (default: 5.0 which is 5% of the starting capital)
"""

# Importing libraries
import os
import json
import secrets
import string
import asyncio
from contextlib import AsyncExitStack
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from openai import AsyncOpenAI
import sendgrid
from sendgrid.helpers.mail import Mail

# Importing the agents SDK
from agents import (
    Agent, Tool, Runner, OpenAIChatCompletionsModel,
    TracingProcessor, Trace, Span,
    trace, add_trace_processor,
)
from agents.mcp import MCPServerStdio

# ── Local ─────────────────────────────────────────────────────────────────────
from accounts import read_accounts_resource, read_strategy_resource, read_account, write_log
from market import is_market_open, is_paid_polygon, is_realtime_polygon

load_dotenv(override=True)

os.makedirs("memory", exist_ok=True)



# Setup the configuration
# This is the configuration for the trading floor
RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
RISK_THRESHOLD_PCT = float(os.getenv("RISK_THRESHOLD_PCT", "5.0"))
MAX_TURNS = 30

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("RISK_EMAIL_FROM")
EMAIL_TO = os.getenv("RISK_EMAIL_TO")

openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Four traders — all routed through OpenRouter paid API
TRADER_NAMES       = ["Warren", "George", "Ray", "Cathie"]
TRADER_LASTNAMES   = ["Patience", "Bold", "Systematic", "Crypto"]
TRADER_MODELS      = [
    "openai/gpt-4o-mini",                    # Warren  — value / patient
    "anthropic/claude-haiku-4-5",            # George  — macro / aggressive
    "openai/gpt-4o-mini",               # Ray     — systematic / balanced
    "meta-llama/llama-3.1-8b-instruct",      # Cathie  — crypto ETF / growth
]
TRADER_SHORT_MODELS = ["GPT-4o Mini", "Claude Haiku", "GPT-4o Mini", "Llama 3.1 8B"]

# Aliases used by app.py
names             = TRADER_NAMES
lastnames         = TRADER_LASTNAMES
short_model_names = TRADER_SHORT_MODELS


def get_model(model_name: str):
    """Route model name to correct client. OpenRouter models contain '/'."""
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    return model_name  # plain name → OpenAI SDK default


# MCP SERVER PARAMSSetup the MCP server parameters
polygon_api_key = os.getenv("POLYGON_API_KEY")
brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}

# Market MCP: use Polygon paid server if available, else local market.py
# This is the market MCP server
if is_paid_polygon or is_realtime_polygon:
    _market_mcp = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": polygon_api_key},
    }
else:
    # market.py now serves both market data AND push notifications as one MCP server
    _market_mcp = {"command": "uv", "args": ["run", "market.py"]}

# Trader MCP servers: accounts (buy/sell/balance) + market+push (prices + notifications)
trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "accounts.py"]},
    _market_mcp,
]


def researcher_mcp_server_params(name: str) -> list:
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]


# Setup the prompt templates
# This is the prompt template for the researcher
# It is used to guide the researcher in their research
# It is also used to guide the trader in their trading
# It is also used to guide the risk manager in their risk management
if is_realtime_polygon:
    _market_note = (
        "You have access to realtime market data tools; use your get_last_trade tool "
        "for the latest trade price. You can also use tools for share information, "
        "trends, technical indicators and fundamentals."
    )
elif is_paid_polygon:
    _market_note = (
        "You have access to market data tools but without access to the trade or quote "
        "tools; use your get_snapshot_ticker tool to get the latest share price on a "
        "15 min delay. You can also use tools for share information, trends, technical "
        "indicators and fundamentals."
    )
else:
    _market_note = (
        "You have access to end of day market data; use your lookup_share_price tool "
        "to get the share price as of the prior close."
    )


def researcher_instructions() -> str:
    return f"""You are a financial researcher. You are able to search the web for interesting financial news,
look for possible trading opportunities, and help with research.
Based on the request, you carry out necessary research and respond with your findings.
Take time to make multiple searches to get a comprehensive overview, and then summarize your findings.
If the web search tool raises an error due to rate limits, then use your other tool that fetches web pages instead.

Important: make use of your knowledge graph to retrieve and store information on companies, websites and market conditions.
Use knowledge graph tools to store and recall entity information; retrieve information you have worked on previously,
and store new information about companies, stocks and market conditions.
Also use it to store web addresses that you find interesting so you can check them later.
Draw on your knowledge graph to build your expertise over time.

If there isn't a specific request, respond with investment opportunities based on searching latest news.
The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def research_tool_description() -> str:
    return (
        "This tool researches online for news and opportunities, "
        "either based on your specific request to look into a certain stock, "
        "or generally for notable financial news and opportunities. "
        "Describe what kind of research you're looking for."
    )


def trader_instructions(name: str) -> str:
    return f"""
You are {name}, a trader on the stock market. Your account is under your name, {name}.
You actively manage your portfolio according to your strategy.
You have access to tools including a researcher to research online for news and opportunities, based on your request.
You also have tools to access financial data for stocks. {_market_note}
And you have tools to buy and sell stocks using your account name {name}.
You can use your entity tools as a persistent memory to store and recall information; you share
this memory with other traders and can benefit from the group's knowledge.
Use these tools to carry out research, make decisions, and execute trades.
After you've completed trading, send a push notification with a brief summary of activity, then reply with a 2-3 sentence appraisal.
Your goal is to maximize your profits according to your strategy.
"""


def trade_message(name: str, strategy: str, account: str) -> str:
    return f"""Based on your investment strategy, you should now look for new opportunities.
Use the research tool to find news and opportunities consistent with your strategy.
Do not use the 'get company news' tool; use the research tool instead.
Use the tools to research stock price and other company information. {_market_note}
Finally, make your decision, then execute trades using the tools.
Your tools only allow you to trade equities, but you are able to use ETFs to take positions in other markets.
You do not need to rebalance your portfolio; you will be asked to do so later.
Just make trades based on your strategy as needed.
Your investment strategy:
{strategy}
Here is your current account:
{account}
Here is the current datetime:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Now, carry out analysis, make your decision and execute trades. Your account name is {name}.
After you've executed your trades, send a push notification with a brief summary of trades and portfolio health, then
respond with a brief 2-3 sentence appraisal of your portfolio and its outlook.
"""


def rebalance_message(name: str, strategy: str, account: str) -> str:
    return f"""Based on your investment strategy, you should now examine your portfolio and decide if you need to rebalance.
Use the research tool to find news and opportunities affecting your existing portfolio.
Use the tools to research stock price and other company information affecting your existing portfolio. {_market_note}
Finally, make your decision, then execute trades using the tools as needed.
You do not need to identify new investment opportunities at this time; you will be asked to do so later.
Just rebalance your portfolio based on your strategy as needed.
Your investment strategy:
{strategy}
You also have a tool to change your strategy if you wish; you can decide at any time that you would like to evolve or switch your strategy.
Here is your current account:
{account}
Here is the current datetime:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Now, carry out analysis, make your decision and execute trades. Your account name is {name}.
After you've executed your trades, send a push notification with a brief summary of trades and portfolio health, then
respond with a brief 2-3 sentence appraisal of your portfolio and its outlook."""


# Setup the tracers
# This is used to log the traces of the agents
ALPHANUM = string.ascii_lowercase + string.digits


def make_trace_id(tag: str) -> str:
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = "".join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"


class LogTracer(TracingProcessor):

    def _get_name(self, obj) -> str | None:
        name = obj.trace_id.split("_")[1]
        return name.split("0")[0] if "0" in name else None

    def _span_msg(self, prefix: str, span: Span) -> str:
        msg = prefix
        if span.span_data:
            if span.span_data.type:
                msg += f" {span.span_data.type}"
            if hasattr(span.span_data, "name") and span.span_data.name:
                msg += f" {span.span_data.name}"
            if hasattr(span.span_data, "server") and span.span_data.server:
                msg += f" {span.span_data.server}"
        if span.error:
            msg += f" {span.error}"
        return msg

    def on_trace_start(self, t) -> None:
        if n := self._get_name(t):
            write_log(n, "trace", f"Started: {t.name}")

    def on_trace_end(self, t) -> None:
        if n := self._get_name(t):
            write_log(n, "trace", f"Ended: {t.name}")

    def on_span_start(self, span: Span) -> None:
        if n := self._get_name(span):
            write_log(n, span.span_data.type if span.span_data else "span", self._span_msg("Started", span))

    def on_span_end(self, span: Span) -> None:
        if n := self._get_name(span):
            write_log(n, span.span_data.type if span.span_data else "span", self._span_msg("Ended", span))

    def force_flush(self) -> None: pass
    def shutdown(self) -> None: pass


# Setup the risk manager
# This is used to monitor the risk of the traders

def _get_initial_balance(data: dict) -> float:
    """Read true starting capital from DB — first entry in portfolio_value_time_series."""
    series = data.get("portfolio_value_time_series", [])
    if series:
        return series[0][1]
    transactions = data.get("transactions", [])
    total_spent = sum(t["quantity"] * t["price"] for t in transactions if t["quantity"] > 0)
    return data.get("balance", 10_000.0) + total_spent


def portfolios_at_risk(traders: list) -> list[str]:
    """Return names of traders who have lost >= RISK_THRESHOLD_PCT of starting capital."""
    at_risk = []
    for trader in traders:
        data = read_account(trader.name.lower())
        if not data:
            continue
        series = data.get("portfolio_value_time_series", [])
        if not series:
            continue
        initial = _get_initial_balance(data)
        latest = series[-1][1]
        if (initial - latest) / initial * 100 >= RISK_THRESHOLD_PCT:
            at_risk.append(trader.name)
    return at_risk


def _send_risk_email(at_risk_names: list[str], report: str):
    """Send the detailed risk report via SendGrid email."""
    if not all([SENDGRID_API_KEY, EMAIL_FROM, EMAIL_TO]):
        print("⚠️  SendGrid not configured. Set SENDGRID_API_KEY, RISK_EMAIL_FROM, RISK_EMAIL_TO in .env")
        return
    at_risk_str = ", ".join(at_risk_names)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"🚨 Risk Alert [{timestamp}]: {at_risk_str} breached loss threshold"
    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto;">
      <h2 style="color: #cc0000;">🚨 Risk Manager Alert</h2>
      <p><strong>Time:</strong> {timestamp}</p>
      <p><strong>Traders at risk:</strong> <span style="color: #cc0000;">{at_risk_str}</span></p>
      <hr/>
      <h3>Risk Assessment Report</h3>
      <pre style="background:#f4f4f4; padding:12px; border-radius:6px; white-space:pre-wrap;">{report}</pre>
      <hr/>
      <p style="color: #888; font-size: 12px;">Sent automatically by your AI Trading Floor Risk Manager.</p>
    </body></html>
    """
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        sg.send(Mail(from_email=EMAIL_FROM, to_emails=EMAIL_TO,
                     subject=subject, html_content=html_body))
        print(f"📧 Risk report emailed to {EMAIL_TO}")
        write_log("risk_manager", "email", f"Report sent to {EMAIL_TO}")
    except Exception as e:
        print(f"❌ Failed to send risk email: {e}")
        write_log("risk_manager", "email_error", str(e))


def _risk_manager_instructions() -> str:
    return f"""You are a professional Risk Manager overseeing a portfolio of four AI traders.
Your role is to protect capital and mitigate losses. You do NOT execute trades.
You assess risk, identify the root causes of losses, and provide clear recommendations.

Your responsibilities:
1. Review the portfolios of all traders who have breached the loss threshold.
2. Identify which positions are causing the losses.
3. Assess whether losses are due to strategy misalignment, market conditions, or concentration risk.
4. Provide specific, actionable recommendations for each at-risk trader.
5. Send a push notification with a brief 1-2 sentence summary (under 200 chars) as a quick heads-up.
6. Reply with a detailed risk report — this will be emailed to the portfolio owner automatically.

You have access to account tools to read balances and holdings.
The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
Push notification example: "⚠️ George & Cathie down 6%. Overexposed to crypto ETFs. Check email."
Your written report should cover: what triggered the alert, which positions are at fault,
specific recommendations per trader, and overall portfolio health.
Write in clear paragraphs — your report will be formatted and sent as an HTML email.
"""


def _build_risk_message(at_risk_names: list[str]) -> str:
    portfolios = []
    for name in TRADER_NAMES:
        data = read_account(name.lower())
        if not data:
            continue
        series = data.get("portfolio_value_time_series", [])
        initial = _get_initial_balance(data)
        latest = series[-1][1] if series else initial
        loss_pct = (initial - latest) / initial * 100
        portfolios.append({
            "name": name,
            "status": "⚠️ AT RISK" if name in at_risk_names else "✅ OK",
            "balance": data.get("balance", 0),
            "holdings": data.get("holdings", {}),
            "initial_balance": round(initial, 2),
            "latest_portfolio_value": round(latest, 2),
            "loss_pct": round(loss_pct, 2),
            "recent_transactions": data.get("transactions", [])[-5:],
        })
    at_risk_str = ", ".join(at_risk_names)
    return f"""The following traders have breached the {RISK_THRESHOLD_PCT}% loss threshold: {at_risk_str}.

Here is a full summary of all trader portfolios:
{json.dumps(portfolios, indent=2)}

Please:
1. Review each at-risk trader's holdings and recent transactions.
2. Use your account tools to get the latest balances and holdings if needed.
3. Identify the specific positions driving the losses.
4. Provide recommendations for each at-risk trader.
5. Send a push notification with a brief summary (under 200 chars).
6. Reply with your full risk assessment report, which will be emailed automatically.

You do NOT have authority to execute trades. Notify and advise only.
"""


class RiskManager:
    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        self.model_name = model_name

    async def run(self, at_risk_names: list[str]):
        try:
            trace_id = make_trace_id("riskmanager")
            with trace("RiskManager-assessment", trace_id=trace_id):
                async with AsyncExitStack() as stack:
                    mcp_servers = [
                        await stack.enter_async_context(
                            MCPServerStdio(params, client_session_timeout_seconds=120)
                        )
                        for params in trader_mcp_server_params
                    ]
                    agent = Agent(
                        name="RiskManager",
                        instructions=_risk_manager_instructions(),
                        model=get_model(self.model_name),
                        mcp_servers=mcp_servers,
                    )
                    result = await Runner.run(
                        agent, _build_risk_message(at_risk_names), max_turns=15
                    )
                    report = result.final_output if result else "No output"
                    write_log("risk_manager", "report", report[:500])
                    print(f"\n📋 Risk Manager Report:\n{report}\n")
                    _send_risk_email(at_risk_names, report)
        except Exception as e:
            print(f"Error running Risk Manager: {e}")
            write_log("risk_manager", "error", str(e))




# TRADER
class Trader:
    def __init__(self, name: str, lastname: str = "Trader", model_name: str = "openai/gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.agent = None
        self.do_trade = True

    async def _get_researcher_tool(self, researcher_mcp_servers) -> Tool:
        researcher = Agent(
            name="Researcher",
            instructions=researcher_instructions(),
            model=get_model(self.model_name),
            mcp_servers=researcher_mcp_servers,
        )
        return researcher.as_tool(
            tool_name="Researcher",
            tool_description=research_tool_description(),
        )

    async def _get_account_report(self) -> str:
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)

    async def _run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        tool = await self._get_researcher_tool(researcher_mcp_servers)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            tools=[tool],
            mcp_servers=trader_mcp_servers,
        )
        account = await self._get_account_report()
        strategy = await read_strategy_resource(self.name)
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run(self):
        try:
            trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
            trace_id = make_trace_id(self.name.lower())
            with trace(trace_name, trace_id=trace_id):
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
                            for params in researcher_mcp_server_params(self.name)
                        ]
                        await self._run_agent(trader_mcp_servers, researcher_mcp_servers)
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade


# TRADING FLOOR — main entry point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_traders() -> List[Trader]:
    return [
        Trader(name, lastname, model)
        for name, lastname, model in zip(TRADER_NAMES, TRADER_LASTNAMES, TRADER_MODELS)
    ]


async def run_loop():
    add_trace_processor(LogTracer())
    traders = create_traders()
    risk_manager = RiskManager(model_name="openai/gpt-4o-mini")

    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            await asyncio.gather(*[trader.run() for trader in traders])

            at_risk = portfolios_at_risk(traders)
            if at_risk:
                print(f"⚠️  Risk threshold breached for: {at_risk}. Calling Risk Manager...")
                await risk_manager.run(at_risk)
            else:
                print(f"✅ All portfolios within {RISK_THRESHOLD_PCT}% threshold. Risk Manager not needed.")
        else:
            print("Market is closed, skipping run.")

        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"🏦 AI Trading Floor — cycle every {RUN_EVERY_N_MINUTES} min")
    print(f"⚠️  Risk Manager triggers at {RISK_THRESHOLD_PCT}% loss per trader")
    print(f"🤖 Models: {list(zip(TRADER_NAMES, TRADER_SHORT_MODELS))}")
    asyncio.run(run_loop())
