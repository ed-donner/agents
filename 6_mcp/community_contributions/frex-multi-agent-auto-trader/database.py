import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

DB = "accounts.db"


with sqlite3.connect(DB) as conn:
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


def write_account(name, account_dict):
    json_data = json.dumps(account_dict)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (name, account)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET account=excluded.account
        ''', (name.lower(), json_data))
        conn.commit()

def read_account(name):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT account FROM accounts WHERE name = ?', (name.lower(),))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

def write_log(name: str, type: str, message: str):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
        ''', (name.lower(), type, message))
        conn.commit()

def read_log(name: str, last_n=10):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT datetime, type, message FROM logs 
            WHERE name = ? 
            ORDER BY datetime DESC
            LIMIT ?
        ''', (name.lower(), last_n))
        return reversed(cursor.fetchall())

def write_market(date: str, data: dict) -> None:
    data_json = json.dumps(data)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO market (date, data)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET data=excluded.data
        ''', (date, data_json))
        conn.commit()

def read_market(date: str) -> dict | None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM market WHERE date = ?', (date,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None


# Risk table helpers 

def write_risk(name: str, data: dict) -> None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO risk (name, circuit_breaker, var_limit, max_position_pct, daily_loss_limit, events, updated)
            VALUES (:name, :circuit_breaker, :var_limit, :max_position_pct, :daily_loss_limit, :events, datetime('now'))
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
        })
        conn.commit()


def read_risk(name: str) -> dict:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM risk WHERE name = ?', (name.lower(),))
        row = cursor.fetchone()
        if row:
            cols = ["name", "circuit_breaker", "var_limit", "max_position_pct", "daily_loss_limit", "events", "updated"]
            d = dict(zip(cols, row))
            d["circuit_breaker"] = bool(d["circuit_breaker"])
            d["events"] = json.loads(d["events"])
            return d
        # Default risk profile
        default = {
            "name": name.lower(),
            "circuit_breaker": False,
            "var_limit": 0.10,
            "max_position_pct": 0.25,
            "daily_loss_limit": 0.05,
            "events": [],
        }
        write_risk(name, default)
        return default


def reset_risk(name: str) -> None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM risk WHERE name = ?', (name.lower(),))
        conn.commit()
