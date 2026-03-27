import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

DB = "groceries.db"


def initialize_db():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groceries_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                available_quantity INTEGER NOT NULL DEFAULT 0,
                consumed_quantity INTEGER NOT NULL DEFAULT 0,
                added_at DATETIME,
                consumed_at DATETIME
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groceries_consumption (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                consumed_at DATETIME DEFAULT (datetime('now'))
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                datetime DATETIME,
                type TEXT,
                message TEXT
            )
        ''')

        conn.commit()


def write_grocery_inventory(name: str, quantity: int) -> None:
    """Insert or update a grocery item's available inventory quantity."""
    now = datetime.now().isoformat()
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO groceries_inventory (name, available_quantity, added_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                available_quantity = excluded.available_quantity,
                added_at = excluded.added_at
        ''', (name.lower(), quantity, now))
        conn.commit()


def write_grocery_consumption(name: str, quantity: int) -> None:
    """Record a consumption event and update inventory."""
    now = datetime.now().isoformat()
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO groceries_consumption (name, quantity, consumed_at)
            VALUES (?, ?, ?)
        ''', (name.lower(), quantity, now))
        cursor.execute('''
            UPDATE groceries_inventory
            SET consumed_quantity = ?,
                available_quantity = available_quantity - ?,
                consumed_at = ?
            WHERE name = ?
        ''', (quantity, quantity, now, name.lower()))
        conn.commit()


def read_grocery(name: str) -> dict | None:
    """Read a single grocery item by name."""
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM groceries_inventory WHERE name = ?',
            (name.lower(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def write_log(name: str, type: str, message: str) -> None:
    """
    Write a log entry to the logs table.

    Args:
        name (str): The name associated with the log
        type (str): The type of log entry
        message (str): The log message
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
        ''', (name.lower(), type, message))
        conn.commit()


def read_log(name: str, last_n: int = 10) -> list:
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
        return list(reversed(cursor.fetchall()))


# Call once at module load
initialize_db()