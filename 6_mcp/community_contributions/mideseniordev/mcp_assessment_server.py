from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("due_diligence_assessment_server")

DB_PATH = Path(__file__).with_name("assessment.db")
SEVERITY_LEVELS = {"low", "medium", "high", "critical"}
VERDICTS = {"buy", "hold", "avoid"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS companies (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sector TEXT NOT NULL,
            thesis TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            verdict TEXT DEFAULT 'hold',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            source TEXT NOT NULL,
            finding TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS risks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            risk TEXT NOT NULL,
            severity TEXT NOT NULL,
            mitigation TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            rationale TEXT NOT NULL,
            horizon TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
        );
        """
    )
    return conn


def ensure_company_exists(cursor: sqlite3.Cursor, symbol: str) -> None:
    row = cursor.execute(
        "SELECT symbol FROM companies WHERE symbol = ?", (symbol.upper(),)
    ).fetchone()
    if not row:
        raise ValueError(
            f"Company {symbol.upper()} is not registered. Call register_company first."
        )


@mcp.tool()
async def register_company(symbol: str, name: str, sector: str, thesis: str) -> str:
    """Create or update a company record before storing due diligence evidence."""
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO companies(symbol, name, sector, thesis, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                sector = excluded.sector,
                thesis = excluded.thesis,
                updated_at = excluded.updated_at
            """,
            (symbol, name.strip(), sector.strip(), thesis.strip(), utc_now()),
        )
    return f"Registered {symbol} for due diligence."


@mcp.tool()
async def save_finding(symbol: str, source: str, finding: str, confidence: int = 3) -> str:
    """Store a research finding with confidence score from 1 (weak) to 5 (strong)."""
    symbol = symbol.upper().strip()
    if confidence < 1 or confidence > 5:
        raise ValueError("Confidence must be between 1 and 5.")

    with get_db() as conn:
        cur = conn.cursor()
        ensure_company_exists(cur, symbol)
        cur.execute(
            """
            INSERT INTO findings(symbol, source, finding, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (symbol, source.strip(), finding.strip(), confidence, utc_now()),
        )
    return f"Stored finding for {symbol}."


@mcp.tool()
async def save_risk(
    symbol: str,
    risk: str,
    severity: Literal["low", "medium", "high", "critical"] = "medium",
    mitigation: str = "No mitigation captured yet.",
) -> str:
    """Store a downside risk and mitigation plan."""
    symbol = symbol.upper().strip()
    if severity not in SEVERITY_LEVELS:
        raise ValueError(f"Invalid severity '{severity}'.")

    with get_db() as conn:
        cur = conn.cursor()
        ensure_company_exists(cur, symbol)
        cur.execute(
            """
            INSERT INTO risks(symbol, risk, severity, mitigation, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (symbol, risk.strip(), severity, mitigation.strip(), utc_now()),
        )
    return f"Stored risk for {symbol}."


@mcp.tool()
async def save_recommendation(
    symbol: str, action: str, rationale: str, horizon: str = "6-12 months"
) -> str:
    """Store a recommended action for the company."""
    symbol = symbol.upper().strip()
    with get_db() as conn:
        cur = conn.cursor()
        ensure_company_exists(cur, symbol)
        cur.execute(
            """
            INSERT INTO recommendations(symbol, action, rationale, horizon, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (symbol, action.strip(), rationale.strip(), horizon.strip(), utc_now()),
        )
    return f"Stored recommendation for {symbol}."


@mcp.tool()
async def finalize_assessment(
    symbol: str, verdict: Literal["buy", "hold", "avoid"], score: int
) -> str:
    """Finalize assessment score (0-100) and verdict."""
    symbol = symbol.upper().strip()
    if verdict not in VERDICTS:
        raise ValueError(f"Invalid verdict '{verdict}'.")
    if score < 0 or score > 100:
        raise ValueError("Score must be between 0 and 100.")

    with get_db() as conn:
        cur = conn.cursor()
        ensure_company_exists(cur, symbol)
        cur.execute(
            """
            UPDATE companies
            SET verdict = ?, score = ?, updated_at = ?
            WHERE symbol = ?
            """,
            (verdict, score, utc_now(), symbol),
        )
    return f"Finalized {symbol} with verdict={verdict}, score={score}."


@mcp.tool()
async def list_company_assessments() -> str:
    """List all tracked companies sorted by score."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT symbol, name, sector, score, verdict, updated_at
            FROM companies
            ORDER BY score DESC, updated_at DESC
            """
        ).fetchall()
    payload = {"count": len(rows), "companies": [dict(row) for row in rows]}
    return json.dumps(payload, indent=2)


@mcp.resource("assessment://company/{symbol}")
async def company_resource(symbol: str) -> str:
    symbol = symbol.upper().strip()
    with get_db() as conn:
        cur = conn.cursor()
        company = cur.execute(
            """
            SELECT symbol, name, sector, thesis, score, verdict, updated_at
            FROM companies
            WHERE symbol = ?
            """,
            (symbol,),
        ).fetchone()
        if not company:
            return json.dumps({"error": f"No company found for {symbol}"}, indent=2)

        findings = cur.execute(
            """
            SELECT source, finding, confidence, created_at
            FROM findings
            WHERE symbol = ?
            ORDER BY created_at DESC
            """,
            (symbol,),
        ).fetchall()
        risks = cur.execute(
            """
            SELECT risk, severity, mitigation, created_at
            FROM risks
            WHERE symbol = ?
            ORDER BY created_at DESC
            """,
            (symbol,),
        ).fetchall()
        recs = cur.execute(
            """
            SELECT action, rationale, horizon, created_at
            FROM recommendations
            WHERE symbol = ?
            ORDER BY created_at DESC
            """,
            (symbol,),
        ).fetchall()

    payload = {
        "company": dict(company),
        "finding_count": len(findings),
        "risk_count": len(risks),
        "recommendation_count": len(recs),
        "findings": [dict(row) for row in findings],
        "risks": [dict(row) for row in risks],
        "recommendations": [dict(row) for row in recs],
    }
    return json.dumps(payload, indent=2)


@mcp.resource("assessment://leaderboard")
async def leaderboard_resource() -> str:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT symbol, name, score, verdict, updated_at
            FROM companies
            ORDER BY score DESC, updated_at DESC
            """
        ).fetchall()
    return json.dumps([dict(row) for row in rows], indent=2)


@mcp.resource("assessment://rubric")
async def rubric_resource() -> str:
    return (
        "# Due Diligence Rubric\n\n"
        "Use this rubric when finalizing score and verdict:\n"
        "- Market quality and growth potential (0-25)\n"
        "- Unit economics and margin resilience (0-20)\n"
        "- Moat and competitive durability (0-20)\n"
        "- Management execution quality (0-15)\n"
        "- Risk-adjusted valuation and downside protection (0-20)\n\n"
        "Verdict guidance:\n"
        "- 80-100: buy\n"
        "- 55-79: hold\n"
        "- 0-54: avoid\n"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
