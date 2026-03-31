import sqlite3
import json
import os
import secrets
import string
import random
from datetime import datetime, timezone
from functools import lru_cache
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any

from dotenv import load_dotenv
from pydantic import BaseModel
from polygon import RESTClient
from agents import TracingProcessor, Trace, Span

load_dotenv(override=True)

# Configuration & Constants
DB = "accounts.db"
INITIAL_BALANCE = 10_000.0
SPREAD = 0.002
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
POLYGON_PLAN = os.getenv("POLYGON_PLAN", "free")
IS_PAID_POLYGON = POLYGON_PLAN == "paid"
IS_REALTIME_POLYGON = POLYGON_PLAN == "realtime"
ALPHANUM = string.ascii_lowercase + string.digits

# Database
def get_db_connection():
    return sqlite3.connect(DB)

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                datetime DATETIME,
                type TEXT,
                message TEXT
            )
        ''')
        cursor.execute('CREATE TABLE IF NOT EXISTS market (date TEXT PRIMARY KEY, data TEXT)')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk (
                name TEXT PRIMARY KEY,
                circuit_breaker INTEGER DEFAULT 0,
                var_limit REAL DEFAULT 0.1,
                max_position_pct REAL DEFAULT 0.25,
                daily_loss_limit REAL DEFAULT 0.05,
                events TEXT DEFAULT '[]',
                updated DATETIME
            )
        ''')
        conn.commit()

init_db()

def write_account(name: str, account_dict: dict):
    json_data = json.dumps(account_dict)
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO accounts (name, account) VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET account=excluded.account
        ''', (name.lower(), json_data))

def read_account(name: str) -> Optional[dict]:
    with get_db_connection() as conn:
        row = conn.execute('SELECT account FROM accounts WHERE name = ?', (name.lower(),)).fetchone()
        return json.loads(row[0]) if row else None

def write_log(name: str, log_type: str, message: str):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, ?, ?, ?)
        ''', (name.lower(), datetime.now(), log_type, message))

def read_log(name: str, limit: int = 100) -> List[Tuple]:
    with get_db_connection() as conn:
        return conn.execute('''
            SELECT datetime, type, message FROM logs 
            WHERE name = ? ORDER BY datetime DESC LIMIT ?
        ''', (name.lower(), limit)).fetchall()

def write_market(date_str: str, data: dict):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO market (date, data) VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET data=excluded.data
        ''', (date_str, json.dumps(data)))

def read_market(date_str: str) -> Optional[dict]:
    with get_db_connection() as conn:
        row = conn.execute('SELECT data FROM market WHERE date = ?', (date_str,)).fetchone()
        return json.loads(row[0]) if row else None

def write_risk(name: str, data: dict):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO risk (name, circuit_breaker, var_limit, max_position_pct, daily_loss_limit, events, updated)
            VALUES (:name, :circuit_breaker, :var_limit, :max_position_pct, :daily_loss_limit, :events, :updated)
            ON CONFLICT(name) DO UPDATE SET 
                circuit_breaker=excluded.circuit_breaker,
                var_limit=excluded.var_limit,
                max_position_pct=excluded.max_position_pct,
                daily_loss_limit=excluded.daily_loss_limit,
                events=excluded.events,
                updated=excluded.updated
        ''', {
            "name": name.lower(),
            "circuit_breaker": int(data.get("circuit_breaker", False)),
            "var_limit": data.get("var_limit", 0.1),
            "max_position_pct": data.get("max_position_pct", 0.25),
            "daily_loss_limit": data.get("daily_loss_limit", 0.05),
            "events": json.dumps(data.get("events", [])),
            "updated": datetime.now()
        })

def read_risk(name: str) -> dict:
    with get_db_connection() as conn:
        row = conn.execute('SELECT * FROM risk WHERE name = ?', (name.lower(),)).fetchone()
        if row:
            cols = ["name", "circuit_breaker", "var_limit", "max_position_pct", "daily_loss_limit", "events", "updated"]
            d = dict(zip(cols, row))
            d["circuit_breaker"] = bool(d["circuit_breaker"])
            d["events"] = json.loads(d["events"])
            return d
        return {"name": name.lower(), "circuit_breaker": False, "var_limit": 0.10, "max_position_pct": 0.25, "daily_loss_limit": 0.05, "events": []}

def reset_risk(name: str):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM risk WHERE name = ?', (name.lower(),))
        conn.execute('DELETE FROM logs WHERE name = ?', (name.lower(),))

# Market data
def is_market_open() -> bool:
    client = RESTClient(POLYGON_API_KEY)
    return client.get_market_status().market == "open"

@lru_cache(maxsize=2)
def get_market_for_prior_date(today_str: str):
    market_data = read_market(today_str)
    if not market_data:
        client = RESTClient(POLYGON_API_KEY)
        probe = client.get_previous_close_agg("SPY")[0]
        last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
        results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
        market_data = {result.ticker: result.close for result in results}
        write_market(today_str, market_data)
    return market_data

def get_share_price(symbol: str) -> float:
    if IS_PAID_POLYGON:
        client = RESTClient(POLYGON_API_KEY)
        result = client.get_snapshot_ticker("stocks", symbol)
        return result.min.close or result.prev_day.close
    else:
        today = datetime.now().date().strftime("%Y-%m-%d")
        return get_market_for_prior_date(today).get(symbol, 0.0)

# Account models
class Transaction(BaseModel):
    symbol: str
    quantity: int
    price: float
    timestamp: str
    rationale: str

    def total(self) -> float: return self.quantity * self.price
    def __repr__(self): return f"{abs(self.quantity)} shares of {self.symbol} at {self.price} each."

class Account(BaseModel):
    name: str
    balance: float
    strategy: str
    holdings: dict[str, int]
    transactions: list[Transaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        fields = read_account(name.lower())
        if not fields:
            fields = {"name": name.lower(), "balance": INITIAL_BALANCE, "strategy": "", "holdings": {}, "transactions": [], "portfolio_value_time_series": []}
            write_account(name, fields)
        return cls(**fields)

    def save(self): write_account(self.name.lower(), self.model_dump())

    def reset(self, strategy: str):
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def calculate_portfolio_value(self) -> float:
        val = self.balance
        for sym, qty in self.holdings.items():
            val += get_share_price(sym) * qty
        return round(val, 2)

    def calculate_profit_loss(self, current_value: float) -> float:
        return round(current_value - INITIAL_BALANCE, 2)

    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> float:
        price = get_share_price(symbol) * (1 + SPREAD)
        cost = price * quantity
        if cost > self.balance: return 0.0
        self.balance -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append(Transaction(symbol=symbol, quantity=quantity, price=round(price, 2), timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rationale=rationale))
        self.save()
        write_log(self.name, "account", f"Bought {quantity} {symbol}")
        return cost

    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> float:
        if self.holdings.get(symbol, 0) < quantity: return 0.0
        price = get_share_price(symbol) * (1 - SPREAD)
        revenue = price * quantity
        self.balance += revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0: del self.holdings[symbol]
        self.transactions.append(Transaction(symbol=symbol, quantity=-quantity, price=round(price, 2), timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rationale=rationale))
        self.save()
        write_log(self.name, "account", f"Sold {quantity} {symbol}")
        return revenue

    def report(self) -> str:
        pv = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pv))
        self.save()
        data = self.model_dump()
        data["total_portfolio_value"] = pv
        data["total_profit_loss"] = self.calculate_profit_loss(pv)
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

# Tracing
def make_trace_id(tag: str) -> str:
    tag += "0"
    pad_len = 32 - len(tag)
    return f"trace_{tag}{''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))}"

class LogTracer(TracingProcessor):
    def get_name(self, trace_or_span: Trace | Span) -> Optional[str]:
        trace_id = trace_or_span.trace_id
        name_part = trace_id.split("_")[1]
        return name_part.split("0")[0] if '0' in name_part else None

    def on_trace_start(self, trace):
        name = self.get_name(trace)
        if name: write_log(name, "trace", f"Started: {trace.name}")

    def on_trace_end(self, trace):
        name = self.get_name(trace)
        if name: write_log(name, "trace", f"Ended: {trace.name}")

    def on_span_start(self, span):
        name = self.get_name(span)
        if name:
            msg = f"Started {span.span_data.type if span.span_data else 'span'}"
            write_log(name, span.span_data.type if span.span_data else "span", msg)

    def on_span_end(self, span):
        name = self.get_name(span)
        if name:
            msg = f"Ended {span.span_data.type if span.span_data else 'span'}"
            write_log(name, span.span_data.type if span.span_data else "span", msg)

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass