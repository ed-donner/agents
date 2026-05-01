import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

DB = "accounts.db"

class Database:
    def __init__(self):
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
            conn.commit()

    def write_account(self, name, account_dict):
        json_data = json.dumps(account_dict)
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (name, account)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET account=excluded.account
            ''', (name.lower(), json_data))
            conn.commit()

    def read_account(self, name):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT account FROM accounts WHERE name = ?', (name.lower(),))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
    
    def write_log(self, name: str, type: str, message: str):
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

    def read_log(self, name: str, last_n=10):
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