"""Memory for resume caching"""

import sqlite3
from datetime import datetime


DB_PATH = "job_hunter.db"


def get_connection():
    """Get a SQLite connection with same-thread disabled for async usage."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resume_cache (
            url TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            cached_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def get_cached_resume(conn: sqlite3.Connection, url: str) -> str | None:
    """Return cached resume text for the given URL, or None if not cached."""
    row = conn.execute(
        "SELECT text FROM resume_cache WHERE url = ?", (url,)
    ).fetchone()
    return row[0] if row else None


def save_resume(conn: sqlite3.Connection, url: str, text: str):
    """Save or update resume text in the cache."""
    conn.execute(
        "INSERT OR REPLACE INTO resume_cache (url, text, cached_at) VALUES (?, ?, ?)",
        (url, text, datetime.now().isoformat())
    )
    conn.commit()


def invalidate_resume(conn: sqlite3.Connection, url: str):
    """Remove a resume from the cache so it will be re-fetched next time."""
    conn.execute("DELETE FROM resume_cache WHERE url = ?", (url,))
    conn.commit()
