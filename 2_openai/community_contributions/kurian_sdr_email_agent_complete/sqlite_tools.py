import sqlite3

DB_FILE = "threads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watched_threads (
            thread_id TEXT PRIMARY KEY,
            email_to TEXT,
            subject TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    conn.execute("""
        CREATE TABLE IF NOT EXISTS gmail_state (
            key TEXT PRIMARY KEY NOT NULL,
            value TEXT NOT NULL
        )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS replied_messages (
        msg_id TEXT PRIMARY KEY, 
        replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    
    )
    """)

    conn.commit()
    conn.close()


def save_thread(thread_id, email_to, subject):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR IGNORE INTO watched_threads (thread_id, email_to, subject) VALUES (?, ?, ?)",
        (thread_id, email_to, subject)
    )
    conn.commit()
    conn.close()


def is_watched_thread(thread_id):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT email_to, subject FROM watched_threads WHERE thread_id = ?",
        (thread_id,)
    ).fetchone()
    conn.close()
    return row


def get_last_history_id():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT value FROM gmail_state WHERE key = 'last_history_id'"
    ).fetchone()
    conn.close()
    return row[0] if row else None


def save_history_id(history_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM gmail_state WHERE key = 'last_history_id'")
    conn.execute(
        "INSERT INTO gmail_state (key, value) VALUES ('last_history_id', ?)",
        (str(history_id),)
    )
    conn.commit()
    conn.close()

def is_replied(msg_id):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT msg_id FROM replied_messages WHERE msg_id = ? ", (msg_id,)).fetchone()
    conn.close()
    return row is not None

def mark_replied(msg_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO replied_messages (msg_id) VALUES (?)", (msg_id, ))
    conn.commit()
    conn.close()