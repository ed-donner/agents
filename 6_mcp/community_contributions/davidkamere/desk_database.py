import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'desk.db'


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS trader_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trader_name TEXT,
                cycle_time TEXT,
                summary TEXT
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS desk_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_type TEXT,
                cycle_time TEXT,
                summary TEXT,
                details TEXT
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS risk_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_time TEXT,
                severity TEXT,
                message TEXT
            )
            '''
        )


def now_str() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log_trader_action(trader_name: str, summary: str):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO trader_actions (trader_name, cycle_time, summary) VALUES (?, ?, ?)',
            (trader_name, now_str(), summary),
        )


def log_desk_review(review_type: str, summary: str, details: str):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO desk_reviews (review_type, cycle_time, summary, details) VALUES (?, ?, ?, ?)',
            (review_type, now_str(), summary, details),
        )


def log_risk_alert(severity: str, message: str):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO risk_alerts (cycle_time, severity, message) VALUES (?, ?, ?)',
            (now_str(), severity, message),
        )


def read_recent_actions(limit: int = 10):
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT cycle_time, trader_name, summary FROM trader_actions ORDER BY id DESC LIMIT ?',
            (limit,),
        ).fetchall()
    return list(reversed(rows))


def read_recent_reviews(limit: int = 10):
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT cycle_time, review_type, summary, details FROM desk_reviews ORDER BY id DESC LIMIT ?',
            (limit,),
        ).fetchall()
    return list(reversed(rows))


def read_recent_alerts(limit: int = 10):
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT cycle_time, severity, message FROM risk_alerts ORDER BY id DESC LIMIT ?',
            (limit,),
        ).fetchall()
    return list(reversed(rows))
