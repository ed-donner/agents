"""SQLite-backed task library keyed by username (separate from LangGraph checkpoint tables)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "sidekick_memory.sqlite"


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_task_library_user ON task_library(username, created_at DESC)"
    )
    conn.commit()


def save_task(username: str, title: str, summary: str, db_path: Path | None = None) -> str:
    uname = (username or "guest").strip() or "guest"
    conn = _connect(db_path)
    try:
        ensure_schema(conn)
        conn.execute(
            "INSERT INTO task_library (username, title, summary, created_at) VALUES (?, ?, ?, ?)",
            (
                uname,
                title.strip()[:500],
                (summary or "")[:8000],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return f"Saved task '{title.strip()[:80]}' for user {uname}."


def list_recent_tasks(username: str, limit: int = 10, db_path: Path | None = None) -> str:
    uname = (username or "guest").strip() or "guest"
    conn = _connect(db_path)
    try:
        ensure_schema(conn)
        rows = conn.execute(
            "SELECT title, summary, created_at FROM task_library WHERE username = ? "
            "ORDER BY id DESC LIMIT ?",
            (uname, limit),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return f"No saved tasks yet for user '{uname}'."
    lines = [f"Recent tasks for {uname}:"]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. [{r['created_at'][:19]}] {r['title']}")
        if r["summary"]:
            snip = (r["summary"] or "").replace("\n", " ")[:200]
            lines.append(f"   {snip}...")
    return "\n".join(lines)
