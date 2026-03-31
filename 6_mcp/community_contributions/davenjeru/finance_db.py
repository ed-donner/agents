import sqlite3
import json
from datetime import datetime

DB = "finance.db"


def _get_conn():
    return sqlite3.connect(DB)


with _get_conn() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (name, category)
        )
    """)
    conn.commit()


def write_transaction(name: str, amount: float, category: str, description: str, txn_type: str) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (name, date, amount, category, description, type) VALUES (?, ?, ?, ?, ?, ?)",
            (name.lower(), now, amount, category, description, txn_type),
        )
        conn.commit()
        return cursor.lastrowid


def read_transactions(name: str, category: str = "", month: str = "") -> list[dict]:
    query = "SELECT id, date, amount, category, description, type FROM transactions WHERE name = ?"
    params: list = [name.lower()]

    if category:
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)
    if month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    query += " ORDER BY date DESC"

    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [
        {"id": r[0], "date": r[1], "amount": r[2], "category": r[3], "description": r[4], "type": r[5]}
        for r in rows
    ]


def write_budget(name: str, category: str, amount: float):
    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO budgets (name, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(name, category) DO UPDATE SET amount=excluded.amount
            """,
            (name.lower(), category, amount),
        )
        conn.commit()


def read_budgets(name: str) -> dict[str, float]:
    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, amount FROM budgets WHERE name = ?", (name.lower(),))
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_spending_by_category(name: str, month: str = "") -> dict[str, float]:
    query = "SELECT category, SUM(amount) FROM transactions WHERE name = ? AND type = 'expense'"
    params: list = [name.lower()]

    if month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    query += " GROUP BY category"

    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_totals(name: str, month: str = "") -> dict[str, float]:
    base = "SELECT type, SUM(amount) FROM transactions WHERE name = ?"
    params: list = [name.lower()]

    if month:
        base += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    base += " GROUP BY type"

    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(base, params)
        results = {row[0]: row[1] for row in cursor.fetchall()}

    income = results.get("income", 0.0)
    expenses = results.get("expense", 0.0)
    return {"income": income, "expenses": expenses, "net": income - expenses}
