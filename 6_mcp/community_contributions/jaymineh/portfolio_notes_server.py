"""
portfolio_notes_server.py — Type 1 MCP Server (fully local, no web calls)

Provides tools to save and retrieve stock research notes in a local SQLite
database, and exposes them as MCP resources so agents can read prior research
as context before making decisions.
"""
import sqlite3
from datetime import datetime
from mcp.server.fastmcp import FastMCP

DB_PATH = "portfolio_notes.db"

mcp = FastMCP("portfolio_notes_server")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT    NOT NULL,
            note       TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn


@mcp.tool()
def save_research_note(symbol: str, note: str) -> str:
    """Save a research note or insight for a stock symbol.

    Args:
        symbol: The stock ticker symbol (e.g. AAPL, TSLA)
        note: The research note, insight, or summary to save
    """
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO notes (symbol, note, created_at) VALUES (?, ?, ?)",
            (symbol.upper(), note, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
    return f"Note saved for {symbol.upper()}"


@mcp.tool()
def get_research_notes(symbol: str) -> str:
    """Retrieve the most recent research notes for a stock symbol.

    Args:
        symbol: The stock ticker symbol (e.g. AAPL, TSLA)
    """
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT note, created_at FROM notes WHERE symbol = ? "
            "ORDER BY created_at DESC LIMIT 10",
            (symbol.upper(),),
        ).fetchall()
    if not rows:
        return f"No notes found for {symbol.upper()}"
    return f"Research notes for {symbol.upper()}:\n" + "\n".join(
        f"[{ts}] {note}" for note, ts in rows
    )


@mcp.tool()
def list_tracked_symbols() -> str:
    """List all stock symbols that have saved research notes, with note counts."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT symbol, COUNT(*) as note_count "
            "FROM notes GROUP BY symbol ORDER BY symbol"
        ).fetchall()
    if not rows:
        return "No symbols tracked yet"
    return "Tracked symbols:\n" + "\n".join(
        f"  {sym}: {count} note(s)" for sym, count in rows
    )


@mcp.resource("notes://{symbol}")
def get_symbol_notes_resource(symbol: str) -> str:
    """Read all research notes for a stock symbol as an MCP resource.

    Args:
        symbol: The stock ticker symbol
    """
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT note, created_at FROM notes WHERE symbol = ? "
            "ORDER BY created_at DESC LIMIT 10",
            (symbol.upper(),),
        ).fetchall()
    if not rows:
        return f"No research notes available for {symbol.upper()}"
    return "\n".join(f"[{ts}] {note}" for note, ts in rows)


if __name__ == "__main__":
    mcp.run(transport="stdio")
