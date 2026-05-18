import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

DB = "accounts.db"


def _get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent write performance
    return conn


with _get_conn() as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            symbol    TEXT NOT NULL,
            quantity  INTEGER NOT NULL,
            price     REAL NOT NULL,
            timestamp TEXT NOT NULL,
            rationale TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT,
            datetime DATETIME,
            type     TEXT,
            message  TEXT
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS market (date TEXT PRIMARY KEY, data TEXT)")
    conn.commit()


def write_account(name: str, account_dict: dict) -> None:
    json_data = json.dumps(account_dict)
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO accounts (name, account) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET account=excluded.account",
            (name.lower(), json_data),
        )
        conn.commit()


def read_account(name: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT account FROM accounts WHERE name = ?", (name.lower(),)
        ).fetchone()
        return json.loads(row[0]) if row else None


def write_transaction(name: str, symbol: str, quantity: int, price: float,
                      timestamp: str, rationale: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO transactions (name, symbol, quantity, price, timestamp, rationale) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name.lower(), symbol, quantity, price, timestamp, rationale),
        )
        conn.commit()


def read_transactions(name: str, last_n: int = 50) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT symbol, quantity, price, timestamp, rationale FROM transactions "
            "WHERE name = ? ORDER BY id DESC LIMIT ?",
            (name.lower(), last_n),
        ).fetchall()
    return [
        {"symbol": r[0], "quantity": r[1], "price": r[2], "timestamp": r[3], "rationale": r[4]}
        for r in reversed(rows)
    ]


def write_log(name: str, type: str, message: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO logs (name, datetime, type, message) VALUES (?, datetime('now'), ?, ?)",
            (name.lower(), type, message),
        )
        conn.commit()


def read_log(name: str, last_n: int = 10, type_filter: str | None = None) -> list[tuple]:
    with _get_conn() as conn:
        if type_filter:
            rows = conn.execute(
                "SELECT datetime, type, message FROM logs WHERE name = ? AND type = ? "
                "ORDER BY datetime DESC LIMIT ?",
                (name.lower(), type_filter, last_n),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT datetime, type, message FROM logs WHERE name = ? "
                "ORDER BY datetime DESC LIMIT ?",
                (name.lower(), last_n),
            ).fetchall()
    return list(reversed(rows))


def write_market(date: str, data: dict) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO market (date, data) VALUES (?, ?) "
            "ON CONFLICT(date) DO UPDATE SET data=excluded.data",
            (date, json.dumps(data)),
        )
        conn.commit()


def read_market(date: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT data FROM market WHERE date = ?", (date,)
        ).fetchone()
        return json.loads(row[0]) if row else None
