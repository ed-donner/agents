import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).resolve().with_name("lead_desk.db")


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB)


with _connect() as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            company TEXT,
            role_title TEXT,
            interest TEXT,
            status TEXT,
            summary TEXT,
            next_action TEXT,
            source_brief TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            lead TEXT
        )
        """
    )
    conn.commit()


def upsert_lead(lead_dict: dict) -> None:
    payload = json.dumps(lead_dict)
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads (
                id, name, email, company, role_title, interest, status,
                summary, next_action, source_brief,
                created_at, updated_at, lead
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                company=excluded.company,
                role_title=excluded.role_title,
                interest=excluded.interest,
                status=excluded.status,
                summary=excluded.summary,
                next_action=excluded.next_action,
                source_brief=excluded.source_brief,
                updated_at=excluded.updated_at,
                lead=excluded.lead
            """,
            (
                lead_dict["id"],
                lead_dict.get("name", ""),
                lead_dict.get("email", ""),
                lead_dict.get("company", ""),
                lead_dict.get("role_title", ""),
                lead_dict.get("interest", ""),
                lead_dict.get("status", "new"),
                lead_dict.get("summary", ""),
                lead_dict.get("next_action", ""),
                lead_dict.get("source_brief", ""),
                lead_dict.get("created_at", datetime.now().isoformat()),
                lead_dict.get("updated_at", datetime.now().isoformat()),
                payload,
            ),
        )
        conn.commit()


def read_lead(lead_id: str) -> dict | None:
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT lead FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None


def list_leads(status: str = "all") -> list[dict]:
    query = "SELECT lead FROM leads"
    params: tuple[str, ...] = ()
    if status != "all":
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY updated_at DESC"

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [json.loads(row[0]) for row in cursor.fetchall()]