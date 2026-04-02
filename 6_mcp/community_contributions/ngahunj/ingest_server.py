from mcp.server.fastmcp import FastMCP
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "policy.db"

mcp = FastMCP("policy_server")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS digests (
        id INTEGER PRIMARY KEY,
        analyst_name TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS policy_events (
        id INTEGER PRIMARY KEY,
        analyst_name TEXT,
        title TEXT,
        jurisdiction TEXT,
        status TEXT,
        impact TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@mcp.tool()
async def save_digest(name: str, content: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO digests VALUES (NULL, ?, ?, ?)",
        (name, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return "saved"


@mcp.tool()
async def get_recent_digests(name: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT content FROM digests WHERE analyst_name=? ORDER BY created_at DESC LIMIT 3",
        (name,),
    ).fetchall()
    conn.close()
    return [r["content"] for r in rows]


@mcp.resource("digests://recent/{name}")
async def read_recent_resource(name: str) -> str:
    conn = get_db()
    rows = conn.execute(
        "SELECT content, created_at FROM digests WHERE analyst_name=? ORDER BY created_at DESC LIMIT 3",
        (name,),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No digests yet for {name}."

    return "\n\n---\n\n".join(f"**{r['created_at']}**\n{r['content']}" for r in rows)


if __name__ == "__main__":
    mcp.run(transport="stdio")
