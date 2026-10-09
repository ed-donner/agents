from mcp.server.fastmcp import FastMCP
import sqlite3
import json
from datetime import datetime

mcp = FastMCP("job_server")


def get_db():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            updated_at TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (symbol) REFERENCES companies(symbol)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            plan TEXT,
            created_at TEXT,
            FOREIGN KEY (symbol) REFERENCES companies(symbol)
        )
        """
    )
    conn.commit()
    return conn


@mcp.tool()
async def save_company(symbol: str, name: str, sector: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO companies (symbol, name, sector, updated_at) VALUES (?, ?, ?, ?)",
        (symbol.upper(), name, sector, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return f"Saved company {symbol}"


@mcp.tool()
async def save_job_note(symbol: str, content: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO job_notes (symbol, content, created_at) VALUES (?, ?, ?)",
        (symbol.upper(), content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return f"Saved job note for {symbol}"


@mcp.tool()
async def save_job_plan(symbol: str, plan: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO job_plans (symbol, plan, created_at) VALUES (?, ?, ?)",
        (symbol.upper(), plan, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return f"Saved job plan for {symbol}"


@mcp.resource("jobs://company/{symbol}")
async def read_company_resource(symbol: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE symbol = ?", (symbol.upper(),))
    company = cursor.fetchone()

    cursor.execute(
        "SELECT content, created_at FROM job_notes WHERE symbol = ? ORDER BY created_at DESC",
        (symbol.upper(),),
    )
    notes = cursor.fetchall()

    cursor.execute(
        "SELECT plan, created_at FROM job_plans WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
        (symbol.upper(),),
    )
    plan = cursor.fetchone()
    conn.close()

    if not company:
        return json.dumps({"error": f"No data for {symbol}"})

    data = {
        "symbol": company["symbol"],
        "name": company["name"],
        "sector": company["sector"],
        "updated_at": company["updated_at"],
        "notes_count": len(notes),
        "notes": [{"content": n["content"], "created_at": n["created_at"]} for n in notes],
        "latest_plan": {"plan": plan["plan"], "created_at": plan["created_at"]} if plan else None,
    }
    return json.dumps(data, indent=2)


@mcp.resource("jobs://all")
async def read_all_companies_resource() -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT symbol, name, sector, updated_at FROM companies ORDER BY updated_at DESC"
    )
    companies = cursor.fetchall()
    conn.close()

    data = {
        "total_companies": len(companies),
        "companies": [dict(c) for c in companies],
    }
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
