"""SQLite store for locally curated Nairobi events."""

import sqlite3
from pathlib import Path

from config import DATA_DIR, DB_PATH


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS local_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            event_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            description TEXT,
            venue TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_event(
    city: str,
    event_name: str,
    event_date: str,
    description: str,
    venue: str,
) -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO local_events (city, event_name, event_date, description, venue)
        VALUES (?, ?, ?, ?, ?)
        """,
        (city, event_name, event_date, description, venue),
    )
    conn.commit()
    conn.close()


def count_events(city: str) -> int:
    if not Path(DB_PATH).exists():
        return 0
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT COUNT(*) FROM local_events WHERE city = ?", (city,)
    )
    n = cur.fetchone()[0]
    conn.close()
    return int(n)


def fetch_events_text(city: str) -> str:
    """Return human-readable upcoming events or an empty marker."""
    if not Path(DB_PATH).exists():
        return f"No upcoming events found for {city}."

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """
        SELECT event_name, event_date, description, venue
        FROM local_events
        WHERE city = ?
        ORDER BY event_date
        LIMIT 12
        """,
        (city,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"No upcoming events found for {city}."

    lines = [f"Local database events for {city}:\n"]
    for name, date, desc, venue in rows:
        lines.append(f"- **{name}** on {date} at {venue}: {desc}")
    return "\n".join(lines)
