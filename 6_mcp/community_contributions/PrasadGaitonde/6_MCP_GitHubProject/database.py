import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "github_agent.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            agent_name TEXT,
            log_type TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def write_log(agent_name: str, log_type: str, message: str):
    timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (timestamp, agent_name, log_type, message)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, agent_name, log_type, message))
    conn.commit()
    conn.close()

# Initialize the database on import
init_db()
