"""
SQLite-backed storage for news articles: save, fetch, list, search, update, delete.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

DEFAULT_DB_PATH = "news.db"


@dataclass
class Article:
    """A news article row. For new inserts, leave id and created_at as None."""

    title: str
    content: str
    topic: str | None = None
    region: str | None = None
    url: str | None = None
    source: str | None = None
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Article:
        return cls(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            topic=row["topic"],
            region=row["region"],
            url=row["url"],
            source=row["source"],
            created_at=row["created_at"],
        )


class NewsRepository:
    """Persists and queries articles in a SQLite database."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT,
                    source TEXT,
                    topic TEXT,
                    region TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()

    def add(self, article: Article) -> Article:
        """Insert an article and return a copy with id and created_at set."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO articles (title, content, url, source, topic, region)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (article.title, article.content, article.url, article.source, article.topic, article.region),
            )
            conn.commit()
            new_id = int(cur.lastrowid)
        loaded = self.get(new_id)
        if loaded is None:
            raise RuntimeError("Inserted article could not be reloaded.")
        return loaded

    def get(self, article_id: int) -> Article | None:
        """Return one article by id, or None if missing."""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id, title, content, url, source, topic, region, created_at FROM articles WHERE id = ?",
                (article_id,),
            )
            row = cur.fetchone()
        return Article.from_row(row) if row else None

    def list_recent(self, limit: int = 5) -> list[Article]:
        """Return the most recent articles, newest first."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, content, url, source, created_at
                FROM articles
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
        return [Article.from_row(r) for r in rows]

    def list_by_region(self, region: str, limit: int = 5) -> list[Article]:
        """Return the most recent articles for a given region, newest first."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, content, url, source, topic, region, created_at
                FROM articles
                WHERE region = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (region, limit),
            )
            rows = cur.fetchall()
        return [Article.from_row(r) for r in rows]

    def delete(self, article_id: int) -> bool:
        """Delete an article by id. Returns True if a row was removed."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            conn.commit()
            return cur.rowcount > 0

    def update(self, article_id: int, **kwargs: Any) -> bool:
        """
        Update fields for an article. Only keys among title, content, url, source
        are applied; others are ignored. Missing keys are left unchanged.
        Use url=None or source=None to set those columns to NULL.

        Returns True if the article existed and was updated (including no-op field sets).
        """
        allowed = {"title", "content", "url", "source"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.get(article_id) is not None
        assignments = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [article_id]
        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE articles SET {assignments} WHERE id = ?",
                values,
            )
            conn.commit()
            return cur.rowcount > 0

    def search(self, query: str) -> list[Article]:
        """
        Return articles where the query matches (case-insensitive) in title, content,
        url, or source. Empty query returns no rows.
        """
        q = query.strip()
        if not q:
            return []
        needle = q.lower()
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, content, url, source, created_at
                FROM articles
                WHERE INSTR(LOWER(title), ?) > 0
                   OR INSTR(LOWER(content), ?) > 0
                   OR INSTR(LOWER(IFNULL(url, '')), ?) > 0
                   OR INSTR(LOWER(IFNULL(source, '')), ?) > 0
                ORDER BY id DESC
                """,
                (needle, needle, needle, needle),
            )
            rows = cur.fetchall()
        return [Article.from_row(r) for r in rows]
