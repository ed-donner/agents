"""
accounts.py

contains:
  - Database layer       (SQLite persistence)
  - Account model        (Pydantic, buy/sell/report logic)
  - Accounts MCP server  (FastMCP — run as: uv run accounts.py)
  - Accounts MCP client  (used by traders.py to read accounts/strategy)
  - Reset logic          (initialise all four traders with their strategies)

Run modes:
  uv run accounts.py            → starts the MCP server (used by trading_floor.py)
  uv run accounts.py --reset    → resets all four trader accounts
"""

# Importing libraries
import sqlite3
import json
import os
import sys
import secrets
import string
from datetime import datetime
from functools import lru_cache

from pydantic import BaseModel
from dotenv import load_dotenv
import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from mcp.server.fastmcp import FastMCP
from agents import FunctionTool

load_dotenv(override=True)



# Setup Database
DB = "accounts.db"

with sqlite3.connect(DB) as _conn:
    _cur = _conn.cursor()
    _cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)")
    _cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            datetime DATETIME,
            type TEXT,
            message TEXT
        )
    """)
    _cur.execute("CREATE TABLE IF NOT EXISTS market (date TEXT PRIMARY KEY, data TEXT)")
    _conn.commit()


def write_account(name: str, account_dict: dict):
    with sqlite3.connect(DB) as conn:
        conn.cursor().execute(
            "INSERT INTO accounts (name, account) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET account=excluded.account",
            (name.lower(), json.dumps(account_dict)),
        )
        conn.commit()


def read_account(name: str) -> dict | None:
    with sqlite3.connect(DB) as conn:
        row = conn.cursor().execute(
            "SELECT account FROM accounts WHERE name = ?", (name.lower(),)
        ).fetchone()
        return json.loads(row[0]) if row else None


def write_log(name: str, type: str, message: str):
    with sqlite3.connect(DB) as conn:
        conn.cursor().execute(
            "INSERT INTO logs (name, datetime, type, message) VALUES (?, datetime('now'), ?, ?)",
            (name.lower(), type, message),
        )
        conn.commit()


def read_log(name: str, last_n: int = 10):
    with sqlite3.connect(DB) as conn:
        rows = conn.cursor().execute(
            "SELECT datetime, type, message FROM logs WHERE name = ? "
            "ORDER BY datetime DESC LIMIT ?",
            (name.lower(), last_n),
        ).fetchall()
        return reversed(rows)


def write_market(date: str, data: dict):
    with sqlite3.connect(DB) as conn:
        conn.cursor().execute(
            "INSERT INTO market (date, data) VALUES (?, ?) "
            "ON CONFLICT(date) DO UPDATE SET data=excluded.data",
            (date, json.dumps(data)),
        )
        conn.commit()


def read_market(date: str) -> dict | None:
    with sqlite3.connect(DB) as conn:
        row = conn.cursor().execute(
            "SELECT data FROM market WHERE date = ?", (date,)
        ).fetchone()
        return json.loads(row[0]) if row else None





# we define the Account model and the Transaction model here

INITIAL_BALANCE = 10_000.0
SPREAD = 0.002  # 0.2% bid/ask spread on every trade


class Transaction(BaseModel):
    symbol: str
    quantity: int
    price: float
    timestamp: str
    rationale: str

    def total(self) -> float:
        return self.quantity * self.price

    def __repr__(self):
        return f"{abs(self.quantity)} shares of {self.symbol} at {self.price} each."


class Account(BaseModel):
    name: str
    balance: float
    strategy: str
    holdings: dict[str, int]
    transactions: list[Transaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        # Import here to avoid circular import at module level
        from market import get_share_price as _gsp
        fields = read_account(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "balance": INITIAL_BALANCE,
                "strategy": "",
                "holdings": {},
                "transactions": [],
                "portfolio_value_time_series": [],
            }
            write_account(name, fields)
        return cls(**fields)

    def save(self):
        write_account(self.name.lower(), self.model_dump())

    def reset(self, strategy: str):
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.save()

    def withdraw(self, amount: float):
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        self.save()

    def _get_price(self, symbol: str) -> float:
        from market import get_share_price
        return get_share_price(symbol)

    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        price = self._get_price(symbol)
        if price == 0:
            raise ValueError(f"Unrecognized symbol {symbol}")
        buy_price = price * (1 + SPREAD)
        total_cost = buy_price * quantity
        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transactions.append(
            Transaction(symbol=symbol, quantity=quantity, price=buy_price,
                        timestamp=timestamp, rationale=rationale)
        )
        self.balance -= total_cost
        self.save()
        write_log(self.name, "account", f"Bought {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        if self.holdings.get(symbol, 0) < quantity:
            raise ValueError(f"Cannot sell {quantity} shares of {symbol}. Not enough held.")
        price = self._get_price(symbol)
        sell_price = price * (1 - SPREAD)
        total_proceeds = sell_price * quantity
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transactions.append(
            Transaction(symbol=symbol, quantity=-quantity, price=sell_price,
                        timestamp=timestamp, rationale=rationale)
        )
        self.balance += total_proceeds
        self.save()
        write_log(self.name, "account", f"Sold {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def calculate_portfolio_value(self) -> float:
        total = self.balance
        for symbol, qty in self.holdings.items():
            total += self._get_price(symbol) * qty
        return total

    def calculate_profit_loss(self, portfolio_value: float) -> float:
        initial_spend = sum(t.total() for t in self.transactions)
        return portfolio_value - initial_spend - self.balance

    def get_holdings(self) -> dict:
        return self.holdings

    def list_transactions(self) -> list:
        return [t.model_dump() for t in self.transactions]

    def report(self) -> str:
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append(
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value)
        )
        self.save()
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump()
        data["total_portfolio_value"] = portfolio_value
        data["total_profit_loss"] = pnl
        write_log(self.name, "account", "Retrieved account details")
        return json.dumps(data)

    def get_strategy(self) -> str:
        write_log(self.name, "account", "Retrieved strategy")
        return self.strategy

    def change_strategy(self, strategy: str) -> str:
        self.strategy = strategy
        self.save()
        write_log(self.name, "account", "Changed strategy")
        return "Changed strategy"





# These are the trader strategies we will use to reset the traders
WARREN_STRATEGY = """
You are Warren, named in homage to Warren Buffett.
You are a value-oriented investor who prioritizes long-term wealth creation.
You identify high-quality companies trading below their intrinsic value.
You invest patiently and hold positions through market fluctuations,
relying on meticulous fundamental analysis, steady cash flows, strong management teams,
and competitive advantages. You rarely react to short-term market movements,
trusting your deep research and value-driven strategy.
"""

GEORGE_STRATEGY = """
You are George, named in homage to George Soros.
You are an aggressive macro trader who actively seeks significant market mispricings.
You look for large-scale economic and geopolitical events that create investment opportunities.
Your approach is contrarian, willing to bet boldly against prevailing market sentiment
when your macroeconomic analysis suggests a significant imbalance.
You leverage careful timing and decisive action to capitalize on rapid market shifts.
"""

RAY_STRATEGY = """
You are Ray, named in homage to Ray Dalio.
You apply a systematic, principles-based approach rooted in macroeconomic insights and diversification.
You invest broadly across asset classes, utilizing risk parity strategies to achieve balanced returns
in varying market environments. You pay close attention to macroeconomic indicators, central bank
policies, and economic cycles, adjusting your portfolio strategically to manage risk and preserve
capital across diverse market conditions.
"""

CATHIE_STRATEGY = """
You are Cathie, named in homage to Cathie Wood.
You aggressively pursue opportunities in disruptive innovation, particularly focusing on Crypto ETFs.
Your strategy is to identify and invest boldly in sectors poised to revolutionize the economy,
accepting higher volatility for potentially exceptional returns. You closely monitor technological
breakthroughs, regulatory changes, and market sentiment in crypto ETFs, ready to take bold positions
and actively manage your portfolio to capitalize on rapid growth trends.
You focus your trading on crypto ETFs.
"""


def reset_traders():
    Account.get("Warren").reset(WARREN_STRATEGY)
    Account.get("George").reset(GEORGE_STRATEGY)
    Account.get("Ray").reset(RAY_STRATEGY)
    Account.get("Cathie").reset(CATHIE_STRATEGY)
    print("✅ All four trader accounts reset successfully.")





# MCP Client  (used by trading_floor.py to read accounts/strategies)
_client_params = StdioServerParameters(
    command="uv", args=["run", "accounts.py"], env=None
)


async def read_accounts_resource(name: str) -> str:
    async with stdio_client(_client_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://accounts_server/{name}")
            return result.contents[0].text


async def read_strategy_resource(name: str) -> str:
    async with stdio_client(_client_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://strategy/{name}")
            return result.contents[0].text


async def _call_accounts_tool(tool_name: str, tool_args: dict):
    async with stdio_client(_client_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return await session.call_tool(tool_name, tool_args)


async def get_accounts_tools_openai() -> list:
    async with stdio_client(_client_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
    openai_tools = []
    for tool in tools_result.tools:
        schema = {**tool.inputSchema, "additionalProperties": False}
        openai_tools.append(FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            on_invoke_tool=lambda ctx, args, tn=tool.name: _call_accounts_tool(tn, json.loads(args)),
        ))
    return openai_tools




# MCP Server  (entry point: uv run accounts.py)
mcp_server = FastMCP("accounts_server")


@mcp_server.tool()
async def get_balance(name: str) -> float:
    """Get the cash balance of the given account name."""
    return Account.get(name).balance


@mcp_server.tool()
async def get_holdings(name: str) -> dict[str, int]:
    """Get the holdings of the given account name."""
    return Account.get(name).holdings


@mcp_server.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Buy shares of a stock.

    Args:
        name: The name of the account holder
        symbol: The symbol of the stock
        quantity: The quantity of shares to buy
        rationale: The rationale for the purchase and fit with the account's strategy
    """
    return Account.get(name).buy_shares(symbol, quantity, rationale)


@mcp_server.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Sell shares of a stock.

    Args:
        name: The name of the account holder
        symbol: The symbol of the stock
        quantity: The quantity of shares to sell
        rationale: The rationale for the sale and fit with the account's strategy
    """
    return Account.get(name).sell_shares(symbol, quantity, rationale)


@mcp_server.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """At your discretion, call this to change your investment strategy for the future.

    Args:
        name: The name of the account holder
        strategy: The new strategy for the account
    """
    return Account.get(name).change_strategy(strategy)


@mcp_server.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    return Account.get(name.lower()).report()


@mcp_server.resource("accounts://strategy/{name}")
async def read_strategy_resource_mcp(name: str) -> str:
    return Account.get(name.lower()).get_strategy()


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_traders()
    else:
        mcp_server.run(transport="stdio")
