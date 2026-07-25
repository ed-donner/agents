"""
Bio Agent — Database Layer
--------------------------
Pure SQLite operations. No LLM awareness.
Handles: faq, conversations, contacts tables.
"""

import os
import sqlite3
from datetime import datetime, timezone

from config import DB_DIR, DB_PATH


# ── Connection Helper ──────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating dir if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # dict-like access to rows
    return conn


# ── Schema Initialisation ─────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they don't already exist."""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS faq (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                question    TEXT    NOT NULL,
                answer      TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_question   TEXT    NOT NULL,
                agent_answer    TEXT    NOT NULL,
                eval_score      INTEGER,
                timestamp       TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT,
                email       TEXT    NOT NULL,
                notes       TEXT,
                timestamp   TEXT    NOT NULL
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ── FAQ Operations ─────────────────────────────────────────────────────

def lookup_faq(question: str) -> str | None:
    """
    Search for an existing FAQ answer that matches the question.
    Returns the answer string if found, None otherwise.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT answer FROM faq WHERE question LIKE ? LIMIT 1",
            (f"%{question}%",),
        )
        row = cursor.fetchone()
        return row["answer"] if row else None
    finally:
        conn.close()


def save_faq(question: str, answer: str) -> None:
    """Promote a high-quality answer into the FAQ table."""
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO faq (question, answer, created_at) VALUES (?, ?, ?)",
            (question, answer, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


# ── Conversation Logging ──────────────────────────────────────────────

def log_conversation(user_question: str, agent_answer: str, eval_score: int) -> None:
    """Record a complete exchange with its evaluation score."""
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO conversations (user_question, agent_answer, eval_score, timestamp) VALUES (?, ?, ?, ?)",
            (user_question, agent_answer, eval_score, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


# ── Contact Management ────────────────────────────────────────────────

def save_contact(email: str, name: str = "", notes: str = "") -> None:
    """Save a user's contact information."""
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO contacts (name, email, notes, timestamp) VALUES (?, ?, ?, ?)",
            (name, email, notes, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
