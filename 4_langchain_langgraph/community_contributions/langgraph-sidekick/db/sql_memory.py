import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def setup_memory(db_path: str = "db/memory.db") -> AsyncSqliteSaver:
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.commit()
    return AsyncSqliteSaver(conn)
