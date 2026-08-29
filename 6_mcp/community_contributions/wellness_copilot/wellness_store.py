"""Local SQLite persistence for mood and journal entries."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "wellness.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS moods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                score INTEGER NOT NULL,
                note TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                text TEXT NOT NULL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS coach_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                summary TEXT NOT NULL,
                trace_meta TEXT
            )
            """
        )
        conn.commit()


init_db()


def log_mood(user_id: str, score: int, note: str | None = None) -> int:
    uid = user_id.strip().lower()
    if score < 1 or score > 5:
        raise ValueError("score must be 1-5")
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO moods (user_id, created_at, score, note) VALUES (?, ?, ?, ?)",
            (uid, now, score, note or ""),
        )
        conn.commit()
        return int(c.lastrowid)


def append_journal(user_id: str, text: str) -> int:
    uid = user_id.strip().lower()
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO journal (user_id, created_at, text) VALUES (?, ?, ?)",
            (uid, now, text.strip()),
        )
        conn.commit()
        return int(c.lastrowid)


def recent_moods(user_id: str, limit: int = 30):
    uid = user_id.strip().lower()
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT created_at, score, note FROM moods
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
            """,
            (uid, limit),
        )
        return c.fetchall()


def recent_journal(user_id: str, limit: int = 20):
    uid = user_id.strip().lower()
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT created_at, text FROM journal
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
            """,
            (uid, limit),
        )
        return c.fetchall()


def log_coach_run(user_id: str, summary: str, trace_meta: dict | None = None):
    uid = user_id.strip().lower()
    now = datetime.now().isoformat(timespec="seconds")
    meta = json.dumps(trace_meta or {})
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO coach_runs (user_id, created_at, summary, trace_meta) VALUES (?, ?, ?, ?)",
            (uid, now, summary[:20000], meta),
        )
        conn.commit()


def recent_coach_runs(user_id: str, limit: int = 10):
    uid = user_id.strip().lower()
    with _conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT created_at, summary FROM coach_runs
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
            """,
            (uid, limit),
        )
        return c.fetchall()


@dataclass
class GroundingScript:
    title: str
    body: str


GROUNDING: dict[str, GroundingScript] = {
    "breathing": GroundingScript(
        "Box breathing (example routine)",
        """1. Breathe in through your nose for 4 counts.
2. Hold gently for 4 counts.
3. Breathe out through your mouth for 4 counts.
4. Hold gently for 4 counts.
Repeat 4–6 rounds at a comfortable pace. This is a common self-regulation pattern, not medical advice.""",
    ),
    "54321": GroundingScript(
        "5-4-3-2-1 grounding",
        """Name quietly to yourself:
• 5 things you can see
• 4 things you can feel
• 3 things you can hear
• 2 things you can smell
• 1 thing you can taste
This is a widely shared coping skill for anchoring attention in the present.""",
    ),
    "sleep_hygiene": GroundingScript(
        "Sleep hygiene tips (general wellness)",
        """General tips often suggested in public health materials:
• Consistent sleep/wake schedule
• Dim screens before bed
• Cool, dark, quiet room
• Limit caffeine late in the day
For clinical sleep problems, consider discussing with a qualified professional.""",
    ),
}


def get_grounding(kind: str) -> str:
    key = kind.lower().strip()
    if key in ("5-4-3-2-1", "five_four_three_two_one"):
        key = "54321"
    script = GROUNDING.get(key)
    if not script:
        names = ", ".join(sorted(GROUNDING.keys()))
        return f"Unknown kind. Choose one of: {names}"
    return f"## {script.title}\n\n{script.body}"
