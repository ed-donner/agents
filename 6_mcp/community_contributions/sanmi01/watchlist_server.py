"""
watchlist_server.py 
Exposes tools to manage a commodity watchlist backed by a local SQLite
database, so the agent can track, retrieve, and clear commodities of interest.
"""

import sqlite3
from datetime import datetime
from mcp.server.fastmcp import FastMCP

DB_PATH = "watchlist.db"
mcp = FastMCP("watchlist_server")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity   TEXT    NOT NULL UNIQUE,
            notes       TEXT,
            added_at    TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn


@mcp.tool()
def add_to_watchlist(commodity: str, notes: str = "") -> str:
    """Add a commodity to the watchlist.

    Args:
        commodity: Name of the commodity (e.g. Maize, Soybean, Crude Oil).
        notes: Optional context or reason for tracking.
    """
    with _conn() as conn:
        try:
            conn.execute(
                "INSERT INTO watchlist (commodity, notes, added_at) VALUES (?, ?, ?)",
                (commodity.strip(), notes.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            conn.commit()
            return f"{commodity} added to watchlist."
        except sqlite3.IntegrityError:
            return f"{commodity} is already on the watchlist."


@mcp.tool()
def get_watchlist() -> str:
    """Retrieve all commodities currently on the watchlist."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT commodity, notes, added_at FROM watchlist ORDER BY added_at DESC"
        ).fetchall()
    if not rows:
        return "Watchlist is empty."
    lines = [f"- {r[0]} (added {r[2]}){': ' + r[1] if r[1] else ''}" for r in rows]
    return "Current watchlist:\n" + "\n".join(lines)


@mcp.tool()
def remove_from_watchlist(commodity: str) -> str:
    """Remove a commodity from the watchlist.

    Args:
        commodity: Name of the commodity to remove.
    """
    with _conn() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE commodity = ? COLLATE NOCASE",
            (commodity.strip(),),
        )
        conn.commit()
    if cur.rowcount:
        return f"{commodity} removed from watchlist."
    return f"{commodity} was not found on the watchlist."


@mcp.tool()
def get_current_date() -> str:
    """Return today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


if __name__ == "__main__":
    mcp.run(transport="stdio")