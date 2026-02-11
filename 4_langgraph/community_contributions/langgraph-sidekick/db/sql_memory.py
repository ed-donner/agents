import os
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def setup_memory(db_path: str = "db/memory.db") -> AsyncSqliteSaver:
    """Initialize Async SQLite memory storage."""
    #os.makedirs(db_path, exist_ok=True)
    # open async connection
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.commit()
    return AsyncSqliteSaver(conn)
