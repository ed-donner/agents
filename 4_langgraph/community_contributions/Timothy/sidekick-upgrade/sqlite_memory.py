import sqlite3
import json
from typing import Any

class SQLiteMemory:
    def __init__(self, db_path="sidekick_memory.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    thread_id TEXT,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY (thread_id, key)
                )
            ''')

    def save(self, thread_id: str, key: str, value: Any):
        with self.conn:
            self.conn.execute(
                "REPLACE INTO memory (thread_id, key, value) VALUES (?, ?, ?)",
                (thread_id, key, json.dumps(value))
            )

    def load(self, thread_id: str, key: str):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT value FROM memory WHERE thread_id=? AND key=?",
            (thread_id, key)
        )
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def clear(self, thread_id: str):
        with self.conn:
            self.conn.execute(
                "DELETE FROM memory WHERE thread_id=?",
                (thread_id,)
            )
