import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(override=True)

# Absolute path relative to this script's location
SCRIPT_DIR = Path(__file__).parent.absolute()
DB = str(SCRIPT_DIR / "accounts.db")

# Simulation time managment with persistent database
def set_simulation_date(date_str: str):
    """Store current simulation date"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO simulation_state (key, value)
            VALUES ('current_date', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        ''', (date_str,))
        conn.commit()

def get_simulation_date() -> str | None:
    """Get current simulation date"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM simulation_state WHERE key = ?', ('current_date',))
        row = cursor.fetchone()
        return row[0] if row else None

def clear_simulation_date():
    """Clear date"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM simulation_state WHERE key = ?', ('current_date',))
        conn.commit()

def get_current_timestamp() -> str:
    """Get current timestamp or simulated timestamp"""
    sim_date = get_simulation_date()
    if sim_date:        
        return f"{sim_date} 16:00:00"
    
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
        CREATE TABLE IF NOT EXISTS simulation_state (
            key TEXT PRIMARY KEY,
            value TEXT
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
    timestamp = get_current_timestamp()
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, ?, ?, ?)
        ''', (name.lower(), timestamp, type, message))
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

def clear_logs(name: str = None):
    """
    Clear log entries for specific or all traders.
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        if name:
            cursor.execute('DELETE FROM logs WHERE name = ?', (name.lower(),))
        else:
            cursor.execute('DELETE FROM logs')
        conn.commit()

def clear_all_logs():
    """Clear all log entries from the database"""
    clear_logs(None)
