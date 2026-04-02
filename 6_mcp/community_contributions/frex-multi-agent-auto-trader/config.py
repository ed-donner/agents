import os
from datetime import datetime
from dotenv import load_dotenv
from mcp import StdioServerParameters
from agents import FunctionTool

load_dotenv(override=True)

# Directory & Plan config
HERE = os.path.dirname(os.path.abspath(__file__))
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
POLYGON_PLAN = os.getenv("POLYGON_PLAN", "free")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

IS_PAID_POLYGON = POLYGON_PLAN == "paid"
IS_REALTIME_POLYGON = POLYGON_PLAN == "realtime"

# MCP server parameters
if IS_PAID_POLYGON or IS_REALTIME_POLYGON:
    market_mcp_params = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": POLYGON_API_KEY},
    }
else:
    market_mcp_params = {
        "command": "python",
        "args": [os.path.join(HERE, "servers.py"), "market"],
    }

trader_mcp_server_params = [
    StdioServerParameters(command="python", args=[os.path.join(HERE, "servers.py"), "accounts"]),
    StdioServerParameters(command="python", args=[os.path.join(HERE, "servers.py"), "push"]),
    StdioServerParameters(command="python", args=[os.path.join(HERE, "servers.py"), "risk"]),
    StdioServerParameters(**market_mcp_params) if isinstance(market_mcp_params, dict) else market_mcp_params
]

risk_manager_mcp_server_params = [
    StdioServerParameters(command="python", args=[os.path.join(HERE, "servers.py"), "risk"])
]

def researcher_mcp_server_params(name: str):
    memory_dir = os.path.join(HERE, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    servers = []
    if BRAVE_API_KEY:
        # Official Brave MCP is the Node package; the PyPI name `mcp-server-brave-search` has no uvx entrypoint.
        servers.append(
            StdioServerParameters(
                command="npx",
                args=["-y", "@brave/brave-search-mcp-server", "--transport", "stdio"],
                env={**os.environ, "BRAVE_API_KEY": BRAVE_API_KEY},
            )
        )
    servers.append(
        StdioServerParameters(
            command="uvx",
            args=["mcp-server-sqlite", "--db-path", os.path.join(memory_dir, f"{name.lower()}_memory.db")],
        )
    )
    return servers

# Agent instructions

def get_market_note():
    if IS_REALTIME_POLYGON:
        return "You have access to realtime market data; use get_last_trade for the latest price."
    elif IS_PAID_POLYGON:
        return "You have access to market data (15min delay); use get_snapshot_ticker."
    return "You have access to end-of-day market data; use get_share_price for the prior close."

def researcher_instructions():
    return f"""You are a financial Research Analyst. Expert at sourcing signals from macro trends and fundamentals.
Operating principles: Insatiable curiosity, analytical skepticism, and pattern recognition.
{get_market_note()}
Workflow: Search multiple sources, synthesize into a coherent outlook, and identify specific tickers."""

def strategist_instructions():
    return """You are an Investment Strategist. Your job is to turn research signals into a portfolio plan.
Principles: Risk-adjusted returns, diversification, and strategic alignment.
Output: Specific buy/sell recommendations with quantity and clear logic."""

def risk_manager_instructions():
    return """You are a Risk Manager. You monitor trader exposure and enforce safety limits.
Workflow: Check reports, evaluate VaR/concentration, and engage circuit breakers if limits are breached."""

def trader_instructions():
    return f"""You are an Execution Trader. You own the final P&L.
Mandatory Sequence: 1. Research -> 2. Strategize -> 3. Check Risk/Circuit Breaker -> 4. Execute -> 5. Notify.
{get_market_note()}"""

# Message templates

def trade_message(name, strategy, account):
    return f"""New trading cycle for {name}.
Strategy: {strategy}
Account Snapshot: {account}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Identify new opportunities and execute according to your sequence."""

def rebalance_message(name, strategy, account):
    return f"""Time to rebalance for {name}.
Focus on existing holdings and strategy alignment: {strategy}
Account Snapshot: {account}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

def risk_manager_message(name, account):
    return f"""Run risk assessment for {name}.
1. Get report -> 2. Evaluate breaches -> 3. Set circuit breaker -> 4. Log events.
Account Snapshot: {account}"""

# Agentic tools

_HANDOFF_PARAMS = {"type": "object", "properties": {}, "additionalProperties": False}


async def _invoke_research_tool(ctx, args: str):
    return researcher_instructions()


async def _invoke_strategist_tool(ctx, args: str):
    return strategist_instructions()


research_tool = FunctionTool(
    name="research_analyst",
    description="Handoff to a research analyst for market signals and ticker ideas.",
    params_json_schema=_HANDOFF_PARAMS,
    on_invoke_tool=_invoke_research_tool,
)

strategist_tool = FunctionTool(
    name="investment_strategist",
    description="Handoff to a strategist to formulate a specific trade plan.",
    params_json_schema=_HANDOFF_PARAMS,
    on_invoke_tool=_invoke_strategist_tool,
)