from mcp.server.fastmcp import FastMCP
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "digest.db"

mcp = FastMCP("digest_server")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysts (
            name TEXT PRIMARY KEY,
            beat TEXT NOT NULL,
            focus_urls TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyst_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    analysts = [
        (
            "Rahul",
            "AI & Technology",
            ["https://news.ycombinator.com", "https://techcrunch.com/category/artificial-intelligence", "https://www.theverge.com/ai-artificial-intelligence"],
        ),
        (
            "Ram",
            "Climate & Energy",
            ["https://www.bbc.com/news/science-environment", "https://insideclimatenews.org", "https://www.carbonbrief.org"],
        ),
        (
            "Ali",
            "Health & Biotech",
            ["https://www.statnews.com", "https://www.biopharmadive.com", "https://medicalxpress.com"],
        ),
        (
            "Soham",
            "Startups & Venture Capital",
            ["https://techcrunch.com/category/startups", "https://venturebeat.com", "https://news.crunchbase.com"],
        ),
    ]
    for name, beat, urls in analysts:
        conn.execute(
            "INSERT OR IGNORE INTO analysts (name, beat, focus_urls, created_at) VALUES (?, ?, ?, ?)",
            (name, beat, json.dumps(urls), datetime.now().isoformat()),
        )
    conn.commit()
    conn.close()


init_db()


@mcp.tool()
async def get_analyst_beat(name: str) -> dict:
    """Get the beat (topic area) and focus URLs for an analyst.

    Args:
        name: The analyst's name
    """
    conn = get_db()
    row = conn.execute("SELECT * FROM analysts WHERE name = ?", (name,)).fetchone()
    conn.close()
    if not row:
        return {"error": f"Analyst {name} not found"}
    return {"name": row["name"], "beat": row["beat"], "focus_urls": json.loads(row["focus_urls"])}


@mcp.tool()
async def save_digest(name: str, content: str) -> str:
    """Save a completed news digest for an analyst.

    Args:
        name: The analyst's name
        content: The markdown-formatted digest content
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO digests (analyst_name, content, created_at) VALUES (?, ?, ?)",
        (name, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return f"Digest saved for {name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


@mcp.tool()
async def get_recent_digests(name: str, n: int = 3) -> list[dict]:
    """Get the N most recent digests written by an analyst.

    Args:
        name: The analyst's name
        n: Number of recent digests to retrieve (default 3)
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT content, created_at FROM digests WHERE analyst_name = ? ORDER BY created_at DESC LIMIT ?",
        (name, n),
    ).fetchall()
    conn.close()
    return [{"content": r["content"], "created_at": r["created_at"]} for r in rows]


@mcp.resource("digests://beat/{name}")
async def read_beat_resource(name: str) -> str:
    conn = get_db()
    row = conn.execute("SELECT * FROM analysts WHERE name = ?", (name,)).fetchone()
    conn.close()
    if not row:
        return f"No analyst named {name} found."
    url_list = "\n".join(f"- {u}" for u in json.loads(row["focus_urls"]))
    return f"## {name}'s Beat: {row['beat']}\n\nFocus URLs:\n{url_list}"


@mcp.resource("digests://recent/{name}")
async def read_recent_resource(name: str) -> str:
    conn = get_db()
    rows = conn.execute(
        "SELECT content, created_at FROM digests WHERE analyst_name = ? ORDER BY created_at DESC LIMIT 3",
        (name,),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No digests yet for {name}."
    return "\n\n---\n\n".join(f"**{r['created_at']}**\n{r['content']}" for r in rows)


if __name__ == "__main__":
    mcp.run(transport="stdio")
