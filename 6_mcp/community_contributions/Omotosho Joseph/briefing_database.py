import sqlite3
import json
from datetime import datetime

DB = "briefings.db"

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporters (
            name TEXT PRIMARY KEY,
            beat TEXT,
            beat_description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter TEXT,
            headline TEXT,
            summary TEXT,
            sources TEXT,
            datetime TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            datetime DATETIME,
            type TEXT,
            message TEXT
        )
    """)
    conn.commit()


def write_reporter(name: str, beat: str, beat_description: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reporters (name, beat, beat_description)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                beat=excluded.beat,
                beat_description=excluded.beat_description
            """,
            (name.lower(), beat, beat_description),
        )
        conn.commit()


def read_reporter(name: str) -> dict | None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, beat, beat_description FROM reporters WHERE name = ?",
            (name.lower(),),
        )
        row = cursor.fetchone()
        if row:
            return {"name": row[0], "beat": row[1], "beat_description": row[2]}
        return None


def write_article(reporter: str, headline: str, summary: str, sources: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO articles (reporter, headline, summary, sources, datetime)
            VALUES (?, ?, ?, ?, ?)
            """,
            (reporter.lower(), headline, summary, sources, now),
        )
        conn.commit()
    return f"Article saved: {headline}"


def read_articles(reporter: str, limit: int = 10) -> list[dict]:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT headline, summary, sources, datetime FROM articles
            WHERE reporter = ?
            ORDER BY datetime DESC
            LIMIT ?
            """,
            (reporter.lower(), limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "headline": r[0],
                "summary": r[1],
                "sources": r[2],
                "datetime": r[3],
            }
            for r in rows
        ]


def read_all_articles_today() -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT reporter, headline, summary, sources, datetime FROM articles
            WHERE datetime LIKE ?
            ORDER BY datetime DESC
            """,
            (f"{today}%",),
        )
        rows = cursor.fetchall()
        return [
            {
                "reporter": r[0],
                "headline": r[1],
                "summary": r[2],
                "sources": r[3],
                "datetime": r[4],
            }
            for r in rows
        ]


def write_log(name: str, type: str, message: str):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
            """,
            (name.lower(), type, message),
        )
        conn.commit()


def read_log(name: str, last_n: int = 13):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT datetime, type, message FROM logs
            WHERE name = ?
            ORDER BY datetime DESC
            LIMIT ?
            """,
            (name.lower(), last_n),
        )
        return list(reversed(cursor.fetchall()))
