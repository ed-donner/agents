"""
SQLite database layer for task scheduling.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                date        TEXT NOT NULL,   -- YYYY-MM-DD
                time        TEXT NOT NULL,   -- HH:MM
                duration_minutes INTEGER NOT NULL DEFAULT 60,
                priority    TEXT NOT NULL DEFAULT 'medium',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def _to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def get_tasks_in_slot(date: str, time: str, duration_minutes: int) -> list[dict]:
    """
    Return tasks that overlap with [time, time+duration) on date.
    Two intervals overlap if: start_a < end_b AND start_b < end_a
    """
    new_start = _to_minutes(time)
    new_end = new_start + duration_minutes

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE date = ?", (date,)
        ).fetchall()

    conflicts = []
    for row in rows:
        task_start = _to_minutes(row["time"])
        task_end = task_start + row["duration_minutes"]
        if new_start < task_end and task_start < new_end:
            conflicts.append(dict(row))
    return conflicts


def save_task(
    title: str,
    description: str,
    date: str,
    time: str,
    duration_minutes: int,
    priority: str,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (title, description, date, time, duration_minutes, priority)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, date, time, duration_minutes, priority),
        )
        conn.commit()
        return cur.lastrowid


def get_all_tasks() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY date, time"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_task(task_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount > 0


def update_task_time(task_id: int, new_date: str, new_time: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE tasks SET date = ?, time = ? WHERE id = ?",
            (new_date, new_time, task_id),
        )
        conn.commit()
        return cur.rowcount > 0


def find_free_slots(date: str, duration_minutes: int, num_slots: int = 5) -> list[str]:
    """
    Find up to `num_slots` free HH:MM slots on `date` for a task of `duration_minutes`.
    Searches between 07:00 and 22:00 in 30-minute increments.
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT time, duration_minutes FROM tasks WHERE date = ? ORDER BY time",
            (date,),
        ).fetchall()

    busy_intervals = []
    for row in rows:
        start = _to_minutes(row["time"])
        end = start + row["duration_minutes"]
        busy_intervals.append((start, end))

    free_slots = []
    # Search 07:00 (420) to 22:00 (1320)
    candidate = 420  # 7:00 AM
    while candidate + duration_minutes <= 1320 and len(free_slots) < num_slots:
        candidate_end = candidate + duration_minutes
        overlap = any(
            candidate < busy_end and busy_start < candidate_end
            for busy_start, busy_end in busy_intervals
        )
        if not overlap:
            h = candidate // 60
            m = candidate % 60
            free_slots.append(f"{h:02d}:{m:02d}")
        candidate += 30  # 30-minute increments

    return free_slots