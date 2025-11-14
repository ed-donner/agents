from mcp.server.fastmcp import FastMCP
import sqlite3
import json
from datetime import datetime

mcp = FastMCP("research_server")

def get_db():
    conn = sqlite3.connect("research.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            updated_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (symbol) REFERENCES companies(symbol)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            thesis TEXT,
            created_at TEXT,
            FOREIGN KEY (symbol) REFERENCES companies(symbol)
        )
    """)
    conn.commit()
    return conn

@mcp.tool()
async def save_company(symbol: str, name: str, sector: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO companies (symbol, name, sector, updated_at) VALUES (?, ?, ?, ?)",
        (symbol.upper(), name, sector, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return f"Saved company {symbol}"

@mcp.tool()
async def save_research(symbol: str, content: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO research (symbol, content, created_at) VALUES (?, ?, ?)",
        (symbol.upper(), content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return f"Saved research for {symbol}"

@mcp.tool()
async def save_thesis(symbol: str, thesis: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO theses (symbol, thesis, created_at) VALUES (?, ?, ?)",
        (symbol.upper(), thesis, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return f"Saved thesis for {symbol}"

@mcp.resource("research://company/{symbol}")
async def read_company_resource(symbol: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE symbol = ?", (symbol.upper(),))
    company = cursor.fetchone()
    
    cursor.execute(
        "SELECT content, created_at FROM research WHERE symbol = ? ORDER BY created_at DESC",
        (symbol.upper(),)
    )
    research_items = cursor.fetchall()
    
    cursor.execute(
        "SELECT thesis, created_at FROM theses WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
        (symbol.upper(),)
    )
    thesis = cursor.fetchone()
    conn.close()
    
    if not company:
        return json.dumps({"error": f"No data for {symbol}"})
    
    data = {
        "symbol": company["symbol"],
        "name": company["name"],
        "sector": company["sector"],
        "updated_at": company["updated_at"],
        "research_count": len(research_items),
        "research": [{"content": r["content"], "created_at": r["created_at"]} for r in research_items],
        "latest_thesis": {"thesis": thesis["thesis"], "created_at": thesis["created_at"]} if thesis else None
    }
    return json.dumps(data, indent=2)

@mcp.resource("research://all")
async def read_all_companies_resource() -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, sector, updated_at FROM companies ORDER BY updated_at DESC")
    companies = cursor.fetchall()
    conn.close()
    
    data = {
        "total_companies": len(companies),
        "companies": [dict(c) for c in companies]
    }
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    mcp.run(transport='stdio')
