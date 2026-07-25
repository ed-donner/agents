import sqlite3

from datetime import datetime

DB_NAME = "user_sessions.db"

def init_db():
    """Creates the table if it doesn't exist."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id INTEGER PRIMARY KEY,
                    session_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def add_session(session_id, sessionName):
    """
    Adds a session or updates the session name if session_id already exists.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
                INSERT INTO user_sessions (session_id, session_name, timestamp)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    session_name=excluded.session_name,
                    timestamp=excluded.timestamp
            ''', (session_id, sessionName, current_time))

            conn.commit()
    except sqlite3.Error as e:
        print(f"Error logging data: {e}")

def get_sessions():
    """Fetches saved sessions."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_sessions ORDER BY timestamp DESC', ())
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching data: {e}")
        return []

def get_session_by_id(session_id):
    """Fetches a saved session by session_id."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_sessions WHERE session_id = ?', (session_id,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error fetching session by id: {e}")
        return None