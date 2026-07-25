from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from asket_mcp.config import get_settings


@dataclass
class Note:
    id: int
    title: str
    body: str
    created_at: str


class NotesStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, check_same_thread=False)

    def _ensure_schema(self) -> None:
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create(self, title: str, body: str) -> Note:
        title = title.strip()
        body = body.strip()
        if not title:
            raise ValueError("title is required")
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)",
                (title, body, now),
            )
            conn.commit()
            nid = int(cur.lastrowid)
        return Note(id=nid, title=title, body=body, created_at=now)

    def list_notes(self, limit: int = 50) -> list[Note]:
        limit = max(1, min(limit, 200))
        with self._lock, self._conn() as conn:
            rows = conn.execute(
                "SELECT id, title, body, created_at FROM notes ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Note(id=r[0], title=r[1], body=r[2], created_at=r[3]) for r in rows]

    def get(self, note_id: int) -> Note | None:
        with self._lock, self._conn() as conn:
            row = conn.execute(
                "SELECT id, title, body, created_at FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()
        if not row:
            return None
        return Note(id=row[0], title=row[1], body=row[2], created_at=row[3])

    def delete(self, note_id: int) -> bool:
        with self._lock, self._conn() as conn:
            cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cur.rowcount > 0


_store: NotesStore | None = None


def get_notes_store() -> NotesStore:
    global _store
    if _store is None:
        p = get_settings().data_dir / "notes.sqlite"
        _store = NotesStore(p)
    return _store


def reset_notes_store_for_tests() -> None:
    global _store
    _store = None
