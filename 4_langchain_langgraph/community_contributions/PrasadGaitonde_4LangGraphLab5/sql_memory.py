"""
SQL-based memory implementation for the Intelligent Data Analysis Agent.
Provides persistent storage for conversations, query history, and user preferences.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json


class SQLMemory:
    """SQLite-based persistent memory for agent conversations and query history."""

    def __init__(self, db_path: str = "./data/agent_memory.db"):
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Sessions table - tracks each analysis session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)

        # Conversations table - stores message history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_role TEXT NOT NULL,
                message_content TEXT NOT NULL,
                message_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Query history table - audit trail of all generated queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                execution_result TEXT,
                execution_error TEXT,
                success BOOLEAN,
                rewrite_attempt INTEGER DEFAULT 0,
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # User preferences table - learns user preferences over time
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, preference_key)
            )
        """)

        # Analysis plans table - stores generated analysis plans
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                plan_steps TEXT NOT NULL,
                target_tables TEXT,
                clarifying_questions TEXT,
                user_clarifications TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_history_session ON query_history(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id)")

        conn.commit()
        conn.close()

    def create_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Create a new analysis session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
                (session_id, user_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def save_message(self, session_id: str, role: str, content: str,
                     message_type: Optional[str] = None) -> bool:
        """Save a conversation message."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (session_id, message_role, message_content, message_type) VALUES (?, ?, ?, ?)",
            (session_id, role, content, message_type)
        )
        conn.commit()
        conn.close()
        return True

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT message_role, message_content, message_type, timestamp
               FROM conversations WHERE session_id = ? ORDER BY timestamp ASC""",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_query(self, session_id: str, sql: str, result: Optional[str] = None,
                   error: Optional[str] = None, rewrite_attempt: int = 0,
                   feedback: Optional[str] = None) -> bool:
        """Save a generated query and its execution result."""
        conn = self._get_connection()
        cursor = conn.cursor()
        success = error is None
        cursor.execute(
            """INSERT INTO query_history
               (session_id, generated_sql, execution_result, execution_error, success, rewrite_attempt, feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, sql, result, error, success, rewrite_attempt, feedback)
        )
        conn.commit()
        conn.close()
        return True

    def get_query_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve query history for a session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT generated_sql, execution_result, execution_error, success,
                      rewrite_attempt, feedback, timestamp
               FROM query_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?""",
            (session_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_user_preference(self, user_id: str, key: str, value: str) -> bool:
        """Save or update a user preference."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO user_preferences (user_id, preference_key, preference_value)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, preference_key)
               DO UPDATE SET preference_value = excluded.preference_value""",
            (user_id, key, value)
        )
        conn.commit()
        conn.close()
        return True

    def get_user_preferences(self, user_id: str) -> Dict[str, str]:
        """Retrieve all preferences for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return {row["preference_key"]: row["preference_value"] for row in rows}

    def save_analysis_plan(self, session_id: str, plan_steps: List[str],
                           target_tables: Optional[List[str]] = None,
                           clarifying_questions: Optional[List[str]] = None,
                           user_clarifications: Optional[str] = None) -> bool:
        """Save an analysis plan."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO analysis_plans
               (session_id, plan_steps, target_tables, clarifying_questions, user_clarifications)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id,
             json.dumps(plan_steps),
             json.dumps(target_tables) if target_tables else None,
             json.dumps(clarifying_questions) if clarifying_questions else None,
             user_clarifications)
        )
        conn.commit()
        conn.close()
        return True

    def get_analysis_plan(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the analysis plan for a session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT plan_steps, target_tables, clarifying_questions, user_clarifications
               FROM analysis_plans WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1""",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "plan_steps": json.loads(row["plan_steps"]),
                "target_tables": json.loads(row["target_tables"]) if row["target_tables"] else None,
                "clarifying_questions": json.loads(row["clarifying_questions"]) if row["clarifying_questions"] else None,
                "user_clarifications": row["user_clarifications"]
            }
        return None

    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status (active, completed, failed)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (status, session_id)
        )
        conn.commit()
        conn.close()
        return True

    def close(self):
        """Close any open connections (called during cleanup)."""
        pass  # SQLite connections are short-lived
