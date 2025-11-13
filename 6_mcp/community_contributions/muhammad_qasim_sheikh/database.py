import sqlite3
import json
import datetime
from pathlib import Path

DB_PATH = Path("audits.db")


def init_db():
    """Initialize the SQLite database if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            title TEXT,
            content TEXT,
            overall_score REAL,
            json_report TEXT
        )
    """)
    conn.commit()
    conn.close()


def write_audit(title: str, content: str, overall_score: float, report: dict):
    """Insert a completed audit result into the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO audits (created_at, title, content, overall_score, json_report)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.utcnow().isoformat(),
            title,
            content[:1000],
            overall_score,
            json.dumps(report, indent=2),
        ),
    )
    conn.commit()
    conn.close()


def list_audits(limit: int = 10):
    """Fetch recent audits."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, title, overall_score FROM audits ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "created_at": r[1], "title": r[2], "overall_score": r[3]}
        for r in rows
    ]


def read_audit(audit_id: int):
    """Retrieve one audit by ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT json_report FROM audits WHERE id=?", (audit_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None
