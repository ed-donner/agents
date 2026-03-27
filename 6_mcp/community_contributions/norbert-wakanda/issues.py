import sqlite3
import os
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issues.db")


def init_db(db_path: str = DB_PATH) -> None:
    """Create the issues table if it doesn't already exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue TEXT NOT NULL,
            command TEXT NOT NULL,
            project_path TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


class IssueStore:
    """Add and search developer issues stored in SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        """Initialise the store, creating the database if needed."""
        self.db_path = db_path
        init_db(db_path)

    def _connect(self) -> sqlite3.Connection:
        """Return a connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_issue(self, issue: str, command: str, project_path: str) -> int:
        """
        Add an issue to the database.

        Returns the id of the newly inserted row.
        """
        conn = self._connect()
        cursor = conn.execute(
            "INSERT INTO issues (issue, command, project_path) VALUES (?, ?, ?)",
            (issue, command, project_path),
        )
        conn.commit()
        issue_id = cursor.lastrowid
        conn.close()
        return issue_id

    def search_issues(self, keywords: list[str], threshold: float = 0.5) -> list[dict]:
        """
        Search for issues where at least 50% of the keywords match
        against the issue, command, or project_path fields.
        Returns a list of matching issue dicts.
        """
        conn = self._connect()
        rows = conn.execute(
            "SELECT id, issue, command, project_path FROM issues"
        ).fetchall()
        conn.close()
        results = []
        for row in rows:
            combined = f"{row['issue']} {row['command']} {row['project_path']}".lower()
            matches = sum(1 for word in keywords if word.lower() in combined)
            if matches / len(keywords) >= threshold:
                results.append(dict(row))
        return results
    def read_log_file(self) -> str:
        """Read and return the contents of the terminal activity log."""
        LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal_activity.log")
        if not os.path.exists(LOG_PATH):
            return ""
        with open(LOG_PATH, "r") as f:
            return f.read().strip()
 
    def clear_log(self) -> str:
        """Empty the terminal activity log file."""
        LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal_activity.log")
        print(f"Log path: {LOG_PATH}")
        open(LOG_PATH, "w").close()
        return f"Log file cleared: {LOG_PATH}"


if __name__ == "__main__":
    init_db()
    print(f"Database created at {DB_PATH}")
