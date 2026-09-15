"""SQLite learner profile for Kirundi study coaching."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class ProfileStore:
    """Persist learner level, goals, and recent mistakes."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    display_name TEXT NOT NULL DEFAULT 'Learner',
                    level TEXT NOT NULL DEFAULT 'A1',
                    goals TEXT NOT NULL DEFAULT '[]',
                    recent_mistakes TEXT NOT NULL DEFAULT '[]',
                    notes TEXT NOT NULL DEFAULT ''
                )
                """
            )
            row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
            if row is None:
                conn.execute("INSERT INTO profile (id) VALUES (1)")
            conn.commit()

    def get(self) -> dict:
        """Return the single learner profile as a dict."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        if row is None:
            return {}
        return {
            "display_name": row["display_name"],
            "level": row["level"],
            "goals": json.loads(row["goals"]),
            "recent_mistakes": json.loads(row["recent_mistakes"]),
            "notes": row["notes"],
        }

    def update(
        self,
        *,
        display_name: str | None = None,
        level: str | None = None,
        goals: list[str] | None = None,
        recent_mistakes: list[str] | None = None,
        notes: str | None = None,
    ) -> dict:
        """Patch profile fields that are provided; return updated profile."""
        current = self.get()
        next_name = display_name if display_name is not None else current["display_name"]
        next_level = level if level is not None else current["level"]
        next_goals = goals if goals is not None else current["goals"]
        next_mistakes = (
            recent_mistakes if recent_mistakes is not None else current["recent_mistakes"]
        )
        next_notes = notes if notes is not None else current["notes"]
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE profile
                SET display_name = ?, level = ?, goals = ?, recent_mistakes = ?, notes = ?
                WHERE id = 1
                """,
                (
                    next_name,
                    next_level,
                    json.dumps(next_goals, ensure_ascii=False),
                    json.dumps(next_mistakes, ensure_ascii=False),
                    next_notes,
                ),
            )
            conn.commit()
        return self.get()
