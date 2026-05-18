from pydantic import BaseModel, Field
from datetime import datetime, timezone
from functools import lru_cache
import uuid
import sqlite3
import json
from typing import List
import os
import requests
from polygon import RESTClient
import random
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from agents import Agent, Runner, trace, handoff, SQLiteSession, function_tool
from mcps import mcp_server_params, TRADING_STRATEGIES, sandbox_path, build_agent_instructions
from agents.mcp import MCPServerStdio
from markdown import markdown
from weasyprint import HTML
from models import Account, Holdings, Transaction, Settings, DEFAULT_STRATEGY, INITIAL_BALANCE, TradeIdeas, Trades, Trade, Idea, QueryItem, QueryList, SharePriceRequest, SharePriceResult


load_dotenv(override=True)



DB = "accounts.db"

settings = Settings()

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
                   (account_id TEXT PRIMARY KEY, 
                    account_name TEXT, 
                    account_type TEXT, 
                    account_balance REAL, 
                    account_currency TEXT, 
                    account_status TEXT, 
                    account_created_at TEXT, 
                    account_updated_at TEXT,
                    account_holdings TEXT,
                    account_strategy TEXT,
                    account_transactions TEXT,
                    account_memory TEXT,
                    account_portfolio_value_time_series TEXT)''')
    cursor.execute('CREATE TABLE IF NOT EXISTS market (date TEXT PRIMARY KEY, data TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                   (name TEXT, 
                    datetime TEXT, 
                    type TEXT, 
                    message TEXT)''')
    conn.commit()





def make_model(provider: str, model_name: str) -> OpenAIChatCompletionsModel:
   
    provider_clients = {
        "openai": lambda: AsyncOpenAI(
            api_key=settings.openai_api_key
        ),
        "deepseek": lambda: AsyncOpenAI(
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key
        ),
        "gemini": lambda: AsyncOpenAI(
            base_url=settings.gemini_base_url,
            api_key=settings.gemini_api_key
        ),
        "groq": lambda: AsyncOpenAI(
            base_url=settings.groq_base_url,
            api_key=settings.groq_api_key
        ),
        "openrouter": lambda: AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        ),
        "ollama": lambda: AsyncOpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama"
        ),
    }

    if provider not in provider_clients:
        raise ValueError(
            f"Unknown provider '{provider}'."
        )

    client = provider_clients[provider]()
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


def serper_search(query: str) -> list:
    headers = {
        "X-API-KEY": settings.serper_api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}

    try:
        response = requests.post(settings.serper_base_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return [
            {
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet")
            }
            for r in data.get("organic", [])
        ]
    except Exception as e:
        print(f"Serper search failed: {e}")
        return []

# def serper_search(queries: QueryList) -> str:
#     headers = {
#         "X-API-KEY": settings.serper_api_key,
#         "Content-Type": "application/json"
#     }

#     try:
#         response = requests.post(
#             settings.serper_base_url,
#             headers=headers,
#             json=queries.model_dump()
#         )
#         response.raise_for_status()
#         data = response.json()

#         results = []

#         if isinstance(data, list):
#             for i, item in enumerate(data):
#                 results.append({
#                     "query": queries.root[i].q,
#                     "results": [
#                         {
#                             "title": r.get("title"),
#                             "link": r.get("link"),
#                             "snippet": r.get("snippet")
#                         }
#                         for r in item.get("organic", [])
#                     ]
#                 })
#         else:
#             results.append({
#                 "query": queries.root[0].q,
#                 "results": [
#                     {
#                         "title": r.get("title"),
#                         "link": r.get("link"),
#                         "snippet": r.get("snippet")
#                     }
#                     for r in data.get("organic", [])
#                 ]
#             })

#         return json.dumps({
#             "status": "ok",
#             "data": results
#         })

#     except Exception as e:
#         return json.dumps({
#             "status": "error",
#             "data": [],
#             "message": str(e)
#         })


def generate_pdf_from_text(
    content: str,
    filename: str,
    is_markdown: bool = True
) -> str:
    """
    Generate a PDF from markdown or HTML content and save it in ./sandbox/

    Args:
        content (str): Markdown or HTML content
        filename (str): Name of the PDF file (e.g. "report.pdf")
        is_markdown (bool): Whether content is markdown (default: True)

    Returns:
        dict: JSON-style response
    """

    try:
        filename = os.path.basename(filename)
        output_path = os.path.join(sandbox_path, filename)

        
        if is_markdown:
            html_content = markdown(content)
        else:
            html_content = content

        
        full_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                p {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        #generate pdf
        HTML(string=full_html).write_pdf(output_path)

        return json.dumps({
            "status": "success",
            "file_path": output_path,
            "message": "PDF saved to sandbox folder"
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

class PolygonClient:
    def __init__(self):
        self.client = RESTClient(api_key=os.getenv("POLYGON_API_KEY"))

    def is_market_open(self) -> bool:
        market_status = self.client.get_market_status()
        return market_status.market == "open"

    def get_all_share_prices_polygon_eod(self) -> dict[str, float]:
        probe = self.client.get_previous_close_agg("SPY")[0]
        last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
        results = self.client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
        return {result.ticker: result.close for result in results}
    
    def get_share_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols in one call using the cached market data."""
        today = datetime.now().date().strftime("%Y-%m-%d")
        market_data = self.get_market_for_prior_date(today)
        return {
            symbol: market_data.get(symbol, 0.0)
            for symbol in symbols
        }

    @lru_cache(maxsize=2)
    def get_market_for_prior_date(self, today: str) -> dict[str, float]:
        market_data = self.read_market(today)
        if not market_data:
            market_data = self.get_all_share_prices_polygon_eod()
            self.write_market(today, market_data)
        return market_data

    def get_share_price_polygon_eod(self, symbol: str) -> float:
        today = datetime.now().date().strftime("%Y-%m-%d")
        market_data = self.get_market_for_prior_date(today)
        return market_data.get(symbol, 0.0)

    def get_share_price_polygon(self, symbol: str) -> float:
        return self.get_share_price_polygon_eod(symbol)

    def get_share_price(self, symbol: str) -> float:
        if os.getenv("POLYGON_API_KEY"):
            try:
                return self.get_share_price_polygon(symbol)
            except Exception as e:
                print(f"Was not able to use the polygon API due to {e}; using a random number")
        return float(random.randint(1, 100))

    def write_market(self, date: str, data: dict) -> None:
        data_json = json.dumps(data)
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO market (date, data)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET data=excluded.data
            ''', (date, data_json))
            conn.commit()

    def read_market(self, date: str) -> dict | None:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM market WHERE date = ?', (date,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None


class AccountManager:
    def __init__(self):
        self.polygon = PolygonClient()

    def get_account(self, account_id: str) -> Account:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE account_id = ?', (account_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Account {account_id} not found")
            holdings = [Holdings(**h) for h in json.loads(row[8])]
            transactions = [Transaction(**t) for t in json.loads(row[10])]
            memory = json.loads(row[11]) if row[11] else []
            portfolio_time_series = [tuple(p) for p in json.loads(row[12])]
            return Account(
                account_id=row[0], account_name=row[1], account_type=row[2],
                account_balance=row[3], account_currency=row[4], account_status=row[5],
                account_created_at=row[6], account_updated_at=row[7], account_holdings=holdings,
                account_strategy=row[9], account_transactions=transactions,
                account_portfolio_value_time_series=portfolio_time_series,
                account_memory=memory
            )

    def create_account(self, account_name: str, account_type: str) -> Account:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT account_id FROM accounts WHERE account_name = ? AND account_type = ?', (account_name, account_type))
            existing = cursor.fetchone()
            if existing:
                return self.get_account(existing[0])
            account_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            cursor.execute('INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (account_id, account_name, account_type, INITIAL_BALANCE, "USD", "active", now, now,
                            json.dumps([]), DEFAULT_STRATEGY, json.dumps([]), json.dumps([]), json.dumps([])))
            conn.commit()
        return self.get_account(account_id)

    def deposit(self, account_id: str, amount: float) -> Account:
        account = self.get_account(account_id)
        if account.account_status != "active":
            raise ValueError("Account is not active")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        new_balance = account.account_balance + amount
        self._update(account_id, account_balance=new_balance)
        return self.get_account(account_id)

    def withdraw(self, account_id: str, amount: float) -> Account:
        account = self.get_account(account_id)
        if account.account_status != "active":
            raise ValueError("Account is not active")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > account.account_balance:
            raise ValueError("Insufficient balance")
        new_balance = account.account_balance - amount
        self._update(account_id, account_balance=new_balance)
        return self.get_account(account_id)

    def get_account_balance(self, account_id: str) -> float:
        account = self.get_account(account_id)
        return account.account_balance

    def get_account_holdings(self, account_id: str) -> List[Holdings]:
        account = self.get_account(account_id)
        return account.account_holdings

    def buy_shares(self, account_id: str, symbol: str, units: int, rationale: str = "") -> Account:
        account = self.get_account(account_id)
        if account.account_status != "active":
            raise ValueError("Account is not active")
        if units <= 0:
            raise ValueError("Units must be positive")
        unit_price = self.polygon.get_share_price(symbol)
        total_cost = units * unit_price
        if total_cost > account.account_balance:
            raise ValueError(f"Insufficient balance. Need ${total_cost:.2f}, have ${account.account_balance:.2f}")
        account.account_holdings.append(Holdings(symbol=symbol, units=units, unit_price=unit_price, total_cost=total_cost))
        account.account_transactions.append(Transaction(symbol=symbol, quantity=units, price=unit_price, timestamp=datetime.now().isoformat(), rationale=rationale))
        new_balance = account.account_balance - total_cost
        self._update(account_id, account_balance=new_balance, account_holdings=account.account_holdings, account_transactions=account.account_transactions)
        return self.get_account(account_id)

    def sell_shares(self, account_id: str, symbol: str, units: int, rationale: str = "") -> Account:
        account = self.get_account(account_id)
        if account.account_status != "active":
            raise ValueError("Account is not active")
        if units <= 0:
            raise ValueError("Units must be positive")
        holdings = [h for h in account.account_holdings if h.symbol == symbol]
        if not holdings:
            raise ValueError(f"No holding found for {symbol}")
        total_units_held = sum(h.units for h in holdings)
        if units > total_units_held:
            raise ValueError(f"Insufficient units. You hold {total_units_held} units of {symbol}")
        unit_price = self.polygon.get_share_price(symbol)
        units_to_sell = units
        for holding in holdings:
            if units_to_sell <= 0:
                break
            if units_to_sell >= holding.units:
                units_to_sell -= holding.units
                account.account_holdings.remove(holding)
            else:
                holding.units -= units_to_sell
                holding.total_cost = holding.units * holding.unit_price
                units_to_sell = 0
        account.account_transactions.append(Transaction(symbol=symbol, quantity=-units, price=unit_price, timestamp=datetime.now().isoformat(), rationale=rationale))
        sale_amount = units * unit_price
        new_balance = account.account_balance + sale_amount
        self._update(account_id, account_balance=new_balance, account_holdings=account.account_holdings, account_transactions=account.account_transactions)
        return self.get_account(account_id)

    def change_strategy(self, account_id: str, strategy: str) -> Account:
        account = self.get_account(account_id)
        if account.account_status != "active":
            raise ValueError("Account is not active")
        self._update(account_id, account_strategy=strategy)
        return self.get_account(account_id)

    def get_account_strategy(self, account_id: str) -> str:
        account = self.get_account(account_id)
        return account.account_strategy

    def calculate_portfolio_value(self, account_id: str) -> float:
        account = self.get_account(account_id)
        symbols = list({h.symbol for h in account.account_holdings})
        current_prices = {symbol: self.polygon.get_share_price(symbol) for symbol in symbols}
        holdings_value = sum(h.units * current_prices.get(h.symbol, h.unit_price) for h in account.account_holdings)
        portfolio_value = account.account_balance + holdings_value
        now = datetime.now().isoformat()
        account.account_portfolio_value_time_series.append((now, portfolio_value))
        self._update(account_id, account_portfolio_value_time_series=account.account_portfolio_value_time_series)
        return portfolio_value

    def calculate_profit_loss(self, account_id: str) -> float:
        account = self.get_account(account_id)
        symbols = list({h.symbol for h in account.account_holdings})
        current_prices = {symbol: self.polygon.get_share_price(symbol) for symbol in symbols}
        return sum(
            h.units * (current_prices.get(h.symbol, h.unit_price) - h.unit_price)
            for h in account.account_holdings
        )

    def get_profit_loss(self, account_id: str) -> dict[str, float]:
        account = self.get_account(account_id)
        symbols = list({h.symbol for h in account.account_holdings})
        current_prices = {symbol: self.polygon.get_share_price(symbol) for symbol in symbols}
        return {
            h.symbol: round(h.units * (current_prices.get(h.symbol, h.unit_price) - h.unit_price), 2)
            for h in account.account_holdings
        }

    def get_portfolio_value_display(self, account_id: str) -> tuple[float, float]:
        """Read-only — calculates value and P&L without saving to time series"""
        account = self.get_account(account_id)
        if not account.account_holdings:
            return account.account_balance, 0.0
        symbols = list({h.symbol for h in account.account_holdings})
        current_prices = {s: self.polygon.get_share_price(s) for s in symbols}
        holdings_value = sum(h.units * current_prices.get(h.symbol, h.unit_price) for h in account.account_holdings)
        pv = account.account_balance + holdings_value
        pl = sum(h.units * (current_prices.get(h.symbol, h.unit_price) - h.unit_price) for h in account.account_holdings)
        return pv, pl

    def list_transactions(self, account_id: str) -> List[Transaction]:
        account = self.get_account(account_id)
        return account.account_transactions

    def report(self, account_id: str) -> str:
        account = self.get_account(account_id)
        portfolio_value = self.calculate_portfolio_value(account_id)
        profit_loss = self.get_profit_loss(account_id)
        return json.dumps({
            "account_id": account.account_id,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "account_strategy": account.account_strategy,
            "account_balance": account.account_balance,
            "account_currency": account.account_currency,
            "portfolio_value": portfolio_value,
            "profit_loss_per_symbol": profit_loss,
            "total_profit_loss": sum(profit_loss.values()),
            "total_holdings": len(account.account_holdings),
            "total_transactions": len(account.account_transactions),
            "account_status": account.account_status,
            "account_created_at": account.account_created_at,
            "account_updated_at": account.account_updated_at,
        })

    def write_log(self, name: str, type: str, message: str) -> None:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (name, datetime, type, message)
                VALUES (?, datetime('now'), ?, ?)
            ''', (name.lower(), type, message))
            conn.commit()

    def read_log(self, name: str, last_n: int = 10) -> list:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT datetime, type, message FROM logs 
                WHERE name = ? 
                ORDER BY datetime DESC
                LIMIT ?
            ''', (name.lower(), last_n))
            return list(reversed(cursor.fetchall()))
    
    def write_memory(self, account_id: str, messages: list) -> None:
        self._update(account_id, account_memory=json.dumps(messages))

    def read_memory(self, account_id: str) -> list:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT account_memory FROM accounts WHERE account_id = ?', (account_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row and row[0] else []

    def _update(self, account_id: str, **fields) -> None:
        fields["account_updated_at"] = datetime.now().isoformat()
        if "account_holdings" in fields:
            fields["account_holdings"] = json.dumps([h.model_dump() for h in fields["account_holdings"]])
        if "account_transactions" in fields:
            fields["account_transactions"] = json.dumps([t.model_dump() for t in fields["account_transactions"]])
        if "account_portfolio_value_time_series" in fields:
            fields["account_portfolio_value_time_series"] = json.dumps(fields["account_portfolio_value_time_series"])
        if "account_memory" in fields:
            if not isinstance(fields["account_memory"], str):
                fields["account_memory"] = json.dumps(fields["account_memory"])
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [account_id]
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE accounts SET {set_clause} WHERE account_id = ?', values)
            conn.commit()

    def send_email(self, subject: str, html_body: str) -> dict:
        """Send an email to the user using Mailgun"""
        domain = os.getenv("MAILGUN_DOMAIN")
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data={
                "from":    os.getenv("MAILGUN_FROM_EMAIL"),
                "to":      [os.getenv("MAILGUN_RECIPIENT")],
                "subject": subject,
                "html":    html_body,
            },
        )
        response.raise_for_status()
        print("Mailgun response:", response.status_code)
        return {"status": "success", "status_code": response.status_code}



class Trader:
    def __init__(self, acct: Account, acct_manager: AccountManager, model=None):
        self.acct = acct
        self.acct_manager = acct_manager
        self.polygon = PolygonClient()
        self.model = model or make_model("openrouter", "openai/gpt-oss-120b:free")
        self.instructions = build_agent_instructions(acct)
        self.session = SQLiteSession(acct.account_id, DB)
        self.mcp_servers = []
        self._trader = None
        self._risk_manager = None
        self._portfolio_manager = None
        self._tools = self._build_pm_tools()


    def _build_pm_tools(self):
        acct_manager = self.acct_manager

        @function_tool
        def pm_report(account_id: str) -> str:
            return acct_manager.report(account_id)

        @function_tool
        def pm_is_market_open() -> bool:
            return self.polygon.is_market_open()
        
        @function_tool
        def lookup_share_prices(request: SharePriceRequest) -> SharePriceResult:
            """Get current prices for multiple stock symbols in one call.
            Call this ONCE with all symbols — never call it multiple times in a session."""
            prices = acct_manager.polygon.get_share_prices(request.symbols)
            return SharePriceResult(prices=prices)

        @function_tool
        def pm_change_strategy(account_id: str, strategy: str) -> str:
            return str(acct_manager.change_strategy(account_id, strategy))
        
        @function_tool
        def get_account_strategy(account_id: str) -> str:
            return acct_manager.get_account_strategy(account_id)

        @function_tool
        def get_current_date() -> str:
            return datetime.now().strftime("%Y-%m-%d")

        # @function_tool
        # def lookup_share_price(symbol: str) -> float:
        #     return acct_manager.polygon.get_share_price(symbol)

        @function_tool
        def search_web(query: str) -> str:
            """Search the web using Serper API."""	
            return serper_search(query)

        
        @function_tool
        def get_account_balance(account_id: str) -> float:
            return acct_manager.get_account_balance(account_id)

        @function_tool
        def get_account_holdings(account_id: str) -> list:
            return [h.model_dump() for h in acct_manager.get_account_holdings(account_id)]

        @function_tool
        def calculate_portfolio_value(account_id: str) -> float:
            return acct_manager.calculate_portfolio_value(account_id)


        return {
    "pm": [pm_report, pm_is_market_open, pm_change_strategy, get_account_strategy, get_current_date, lookup_share_prices, search_web, get_account_holdings],
    "risk_manager": [get_account_balance, calculate_portfolio_value],
}

    def trader_agent(self) -> Agent:
        if self._trader is None:
            self._trader = Agent(
                name="Trader",
                instructions=self.instructions["trader"],
                model=self.model,
                mcp_servers=self.mcp_servers,
                handoff_description="Execute approved trades by placing buy/sell orders as specified. Update portfolio records, log all transactions, and generate a trade report. Send the report via email and trigger PDF creation. Do not modify or reinterpret trade decisions."
            )
        return self._trader

    def risk_manager_agent(self) -> Agent:
        if self._risk_manager is None:
            self._risk_manager = Agent(
                name="RiskManager",
                instructions=self.instructions["risk_manager"],
                model=self.model,
                tools=self._tools["risk_manager"],
                output_type= Trades,
                mcp_servers=[],
            )
        return self._risk_manager


    def portfolio_manager_agent(self) -> Agent:
        if self._portfolio_manager is None:
            self._portfolio_manager = Agent(
                name="PortfolioManager",
                instructions=self.instructions["portfolio_manager"],
                model=self.model,
                output_type= Trades,
                tools=[
                    *self._tools["pm"],
                    self.risk_manager_agent().as_tool(
                        tool_name="approve_trades",
                        tool_description="Review proposed trades against risk rules and return approved or rejected list",
                        max_turns=5
                    ),
                ],
                handoffs=[handoff(self.trader_agent())],
            )
        return self._portfolio_manager

    async def run(self) -> str:
        self.mcp_servers = [
            MCPServerStdio(params, client_session_timeout_seconds=30)
            for params in mcp_server_params()
        ]

        for server in self.mcp_servers:
            await server.connect()

        
        self._trader = None
        self._risk_manager = None
        self._researcher = None
        self._portfolio_manager = None

        starting_agent = self.portfolio_manager_agent()

        user_message = f"Start a new trading session for account: {self.acct}"
        

        with trace("TradingSession"):
            result = await Runner.run(
                starting_agent,
                user_message,
                session=self.session,
                max_turns=15
            )

        return result.final_output


# # usage
# account_manager = AccountManager()
# acct = account_manager.create_account("Naheem", "SAV1")
# trader = Trader(acct)
# result = await trader.run()
# display(Markdown(result))