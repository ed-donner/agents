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
        CREATE TABLE IF NOT EXISTS company_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trader_name TEXT,
            symbol TEXT,
            datetime DATETIME,
            rationale TEXT,
            action TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime DATETIME,
            assessment TEXT,
            recommendations TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime DATETIME,
            symbol TEXT,
            headline TEXT,
            sentiment TEXT,
            affected_traders TEXT
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
    """
    Write a log entry to the logs table.
    
    Args:
        name (str): The name associated with the log
        type (str): The type of log entry
        message (str): The log message
    """
    now = datetime.now().isoformat()
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
        ''', (name.lower(), type, message))
        conn.commit()

def read_log(name: str, last_n=10):
    """
    Read the most recent log entries for a given name.
    
    Args:
        name (str): The name to retrieve logs for
        last_n (int): Number of most recent entries to retrieve
        
    Returns:
        list: A list of tuples containing (datetime, type, message)
    """
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

def write_company_insight(trader_name: str, symbol: str, rationale: str, action: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO company_insights (trader_name, symbol, datetime, rationale, action)
            VALUES (?, ?, datetime('now'), ?, ?)
        ''', (trader_name.lower(), symbol.upper(), rationale, action))
        conn.commit()

def read_company_insights(symbol: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT trader_name, datetime, rationale, action FROM company_insights
            WHERE symbol = ?
            ORDER BY datetime DESC
        ''', (symbol.upper(),))
        return cursor.fetchall()

def read_trader_company_insights(trader_name: str, symbol: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT datetime, rationale, action FROM company_insights
            WHERE trader_name = ? AND symbol = ?
            ORDER BY datetime DESC
            LIMIT 5
        ''', (trader_name.lower(), symbol.upper()))
        return cursor.fetchall()

def write_risk_assessment(assessment: str, recommendations: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO risk_assessments (datetime, assessment, recommendations)
            VALUES (datetime('now'), ?, ?)
        ''', (assessment, recommendations))
        conn.commit()

def read_latest_risk_assessment():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT datetime, assessment, recommendations FROM risk_assessments
            ORDER BY datetime DESC
            LIMIT 1
        ''')
        return cursor.fetchone()

def read_all_risk_assessments(last_n=10):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT datetime, assessment, recommendations FROM risk_assessments
            ORDER BY datetime DESC
            LIMIT ?
        ''', (last_n,))
        return cursor.fetchall()

def write_news_alert(symbol: str, headline: str, sentiment: str, affected_traders: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO news_alerts (datetime, symbol, headline, sentiment, affected_traders)
            VALUES (datetime('now'), ?, ?, ?, ?)
        ''', (symbol.upper(), headline, sentiment, affected_traders))
        conn.commit()

def read_latest_news_alerts(last_n=20):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT datetime, symbol, headline, sentiment, affected_traders FROM news_alerts
            ORDER BY datetime DESC
            LIMIT ?
        ''', (last_n,))
        return cursor.fetchall()

def get_connection():
    return sqlite3.connect(DB)