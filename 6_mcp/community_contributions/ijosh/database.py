"""
CARI ── SQLite Persistence Layer
Tables: users · transactions · notifications_log
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cari.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    TEXT PRIMARY KEY,
            business   TEXT NOT NULL,
            email      TEXT DEFAULT '',
            phone      TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT    NOT NULL,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            type        TEXT    NOT NULL CHECK(type IN ('income','expense')),
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notifications_log (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  TEXT NOT NULL,
            channel  TEXT NOT NULL,
            message  TEXT NOT NULL,
            status   TEXT NOT NULL,
            sent_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ── Users ─────────────────────────────────────────────────────
def upsert_user(user_id, business, email="", phone=""):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO users (user_id, business, email, phone)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            business = excluded.business,
            email    = excluded.email,
            phone    = excluded.phone
        """,
        (user_id, business, email, phone),
    )
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Transactions ──────────────────────────────────────────────
def save_transaction(user_id, description, amount, tx_type, category):
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT INTO transactions (user_id, description, amount, type, category, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            description,
            amount,
            tx_type,
            category,
            datetime.now().strftime("%Y-%m-%d"),
        ),
    )
    tx_id = cur.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def get_summary(user_id, month=None):
    period = month or datetime.now().strftime("%Y-%m")
    conn = get_conn()

    rows = conn.execute(
        """
        SELECT type, category, SUM(amount) as total, COUNT(*) as cnt
        FROM transactions
        WHERE user_id=? AND date LIKE ?
        GROUP BY type, category
        ORDER BY type, total DESC
        """,
        (user_id, f"{period}%"),
    ).fetchall()

    recent = conn.execute(
        """
        SELECT * FROM transactions
        WHERE user_id=? AND date LIKE ?
        ORDER BY created_at DESC LIMIT 20
        """,
        (user_id, f"{period}%"),
    ).fetchall()

    conn.close()

    total_income = sum(r["total"] for r in rows if r["type"] == "income")
    total_expense = sum(r["total"] for r in rows if r["type"] == "expense")

    return {
        "period": period,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "breakdown": [dict(r) for r in rows],
        "recent_tx": [dict(r) for r in recent],
    }


def get_all_transactions(user_id):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT date, type, category, description, amount
        FROM transactions WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Notifications log ─────────────────────────────────────────
def log_notification(user_id, channel, message, status):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO notifications_log (user_id, channel, message, status)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, channel, message, status),
    )
    conn.commit()
    conn.close()
