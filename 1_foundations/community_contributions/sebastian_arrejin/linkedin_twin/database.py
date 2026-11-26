import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL UNIQUE,
    answer TEXT NOT NULL,
    times_used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS unknown_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    name TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);
"""


def _connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    with closing(_connect()) as connection:
        connection.executescript(SCHEMA)


def search_faq(query, limit=5):
    """Keyword search: ranks FAQ entries by how many words of the query appear in the question."""
    words = [word for word in re.findall(r"\w+", query.lower()) if len(word) > 3]
    if not words:
        return []
    hits = " + ".join("(instr(lower(question), ?) > 0)" for _ in words)
    sql = f"""
        SELECT id, question, answer FROM (
            SELECT id, question, answer, times_used, ({hits}) AS hits FROM faq
        ) WHERE hits > 0 ORDER BY hits DESC, times_used DESC LIMIT ?
    """
    with closing(_connect()) as connection, connection:
        rows = connection.execute(sql, [*words, limit]).fetchall()
        connection.executemany("UPDATE faq SET times_used = times_used + 1 WHERE id = ?", [(row["id"],) for row in rows])
    return [{"question": row["question"], "answer": row["answer"]} for row in rows]


def save_faq(question, answer):
    with closing(_connect()) as connection, connection:
        connection.execute(
            """INSERT INTO faq (question, answer, created_at) VALUES (?, ?, ?)
               ON CONFLICT(question) DO UPDATE SET answer = excluded.answer""",
            (question, answer, _now()),
        )


def record_unknown_question(question):
    with closing(_connect()) as connection, connection:
        connection.execute(
            "INSERT INTO unknown_questions (question, created_at) VALUES (?, ?)", (question, _now())
        )


def record_contact(email, name, notes):
    with closing(_connect()) as connection, connection:
        connection.execute(
            "INSERT INTO contacts (email, name, notes, created_at) VALUES (?, ?, ?, ?)",
            (email, name, notes, _now()),
        )


def fetch_rows(table):
    queries = {
        "faq": "SELECT question, answer, times_used, created_at FROM faq ORDER BY times_used DESC",
        "unknown_questions": "SELECT question, created_at FROM unknown_questions ORDER BY id DESC",
        "contacts": "SELECT email, name, notes, created_at FROM contacts ORDER BY id DESC",
    }
    with closing(_connect()) as connection:
        return [list(row) for row in connection.execute(queries[table]).fetchall()]
