"""MCP (stdio): local process, local data — SQLite notes in ./data/notes.db."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("najeeb_local_notes")

_DATA_DIR = Path(__file__).resolve().parent / "data"
_DB_PATH = _DATA_DIR / "notes.db"


def _conn() -> sqlite3.Connection:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(_DB_PATH)
    cx.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    cx.commit()
    return cx


@mcp.tool()
async def save_local_note(title: str, body: str) -> str:
    """Save a note to the local SQLite database. No network calls.

    Args:
        title: Short title for the note.
        body: Note content.
    """
    with _conn() as cx:
        cur = cx.execute(
            "INSERT INTO notes (title, body) VALUES (?, ?)", (title.strip(), body.strip())
        )
        cx.commit()
        note_id = cur.lastrowid
    return f"Saved note id={note_id} (local file: {_DB_PATH})"


@mcp.tool()
async def list_local_notes(limit: int = 10) -> str:
    """List recent notes from the local SQLite database (newest first).

    Args:
        limit: Maximum number of rows to return (default 10).
    """
    lim = max(1, min(int(limit), 50))
    with _conn() as cx:
        rows = cx.execute(
            "SELECT id, title, body, created_at FROM notes ORDER BY id DESC LIMIT ?",
            (lim,),
        ).fetchall()
    if not rows:
        return "No notes yet."
    lines = [f"[{r[0]}] {r[1]} ({r[3]})\n{r[2][:500]}" for r in rows]
    return "\n\n---\n\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
