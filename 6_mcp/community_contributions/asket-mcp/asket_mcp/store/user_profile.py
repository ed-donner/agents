from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from asket_mcp.config import get_settings


@dataclass
class StudyProfile:
    goals: str
    expertise_level: str
    roadmap_markdown: str
    updated_at: str


class UserProfileStore:
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
                CREATE TABLE IF NOT EXISTS study_profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    goals TEXT NOT NULL DEFAULT '',
                    expertise_level TEXT NOT NULL DEFAULT '',
                    roadmap_markdown TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO study_profile (id, goals, expertise_level, roadmap_markdown, updated_at) "
                "VALUES (1, '', '', '', '')"
            )
            conn.commit()

    def get_profile(self) -> StudyProfile:
        with self._lock, self._conn() as conn:
            row = conn.execute(
                "SELECT goals, expertise_level, roadmap_markdown, updated_at FROM study_profile WHERE id = 1"
            ).fetchone()
        if not row:
            return StudyProfile("", "", "", "")
        return StudyProfile(row[0], row[1], row[2], row[3])

    def upsert(
        self,
        *,
        goals: str | None = None,
        expertise_level: str | None = None,
        roadmap_markdown: str | None = None,
    ) -> StudyProfile:
        current = self.get_profile()
        g = current.goals if goals is None else goals
        e = current.expertise_level if expertise_level is None else expertise_level
        r = current.roadmap_markdown if roadmap_markdown is None else roadmap_markdown
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                UPDATE study_profile SET goals = ?, expertise_level = ?, roadmap_markdown = ?, updated_at = ?
                WHERE id = 1
                """,
                (g, e, r, now),
            )
            conn.commit()
        return StudyProfile(g, e, r, now)


_profile_store: UserProfileStore | None = None


def get_user_profile_store() -> UserProfileStore:
    global _profile_store
    if _profile_store is None:
        _profile_store = UserProfileStore(get_settings().data_dir / "study_profile.sqlite")
    return _profile_store


def reset_user_profile_store_for_tests() -> None:
    global _profile_store
    _profile_store = None
