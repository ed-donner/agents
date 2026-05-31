import aiosqlite
import os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")


async def setup_memory() -> AsyncSqliteSaver:
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.commit()
    return AsyncSqliteSaver(conn)


async def init_preferences_table():
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.commit()
    await conn.close()


async def load_preferences() -> dict:
    conn = await aiosqlite.connect(DB_PATH)
    cursor = await conn.execute("SELECT key, value FROM user_preferences")
    rows = await cursor.fetchall()
    await conn.close()
    return {row[0]: row[1] for row in rows}


async def save_preferences(preferences: dict):
    conn = await aiosqlite.connect(DB_PATH)
    for key, value in preferences.items():
        await conn.execute(
            """INSERT INTO user_preferences (key, value, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value),
        )
    await conn.commit()
    await conn.close()
