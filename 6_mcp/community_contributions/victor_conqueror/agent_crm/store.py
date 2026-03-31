"""SQLite persistence for deals and touchpoints."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "agent_crm.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rep_name TEXT NOT NULL,
                account_name TEXT NOT NULL,
                stage TEXT NOT NULL DEFAULT 'discovery',
                value_cents INTEGER,
                notes TEXT,
                gmail_thread_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(rep_name, account_name)
            );
            CREATE INDEX IF NOT EXISTS idx_deals_rep ON deals(rep_name);
            CREATE INDEX IF NOT EXISTS idx_deals_thread ON deals(gmail_thread_id);

            CREATE TABLE IF NOT EXISTS touchpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                summary TEXT NOT NULL,
                source_ref TEXT,
                occurred_at TEXT NOT NULL,
                FOREIGN KEY (deal_id) REFERENCES deals(id)
            );
            CREATE INDEX IF NOT EXISTS idx_touch_deal ON touchpoints(deal_id);
            """
        )
        conn.commit()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_deal(
    rep_name: str,
    account_name: str,
    stage: str = "discovery",
    value_dollars: float | None = None,
    notes: str | None = None,
) -> int:
    init_db()
    rep_name = rep_name.strip()
    account_name = account_name.strip()
    vc = int(round(value_dollars * 100)) if value_dollars is not None else None
    now = _utc_now()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM deals WHERE rep_name = ? COLLATE NOCASE AND account_name = ? COLLATE NOCASE",
            (rep_name, account_name),
        ).fetchone()
        if row:
            did = int(row["id"])
            conn.execute(
                """
                UPDATE deals SET stage = ?, value_cents = ?, notes = COALESCE(?, notes), updated_at = ?
                WHERE id = ?
                """,
                (stage, vc, notes, now, did),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO deals (rep_name, account_name, stage, value_cents, notes, gmail_thread_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (rep_name, account_name, stage, vc, notes, now, now),
            )
            did = int(cur.lastrowid)
        conn.commit()
    return did


def link_gmail_thread(deal_id: int, thread_id: str) -> str:
    init_db()
    now = _utc_now()
    with _connect() as conn:
        conn.execute(
            "UPDATE deals SET gmail_thread_id = ?, updated_at = ? WHERE id = ?",
            (thread_id.strip(), now, deal_id),
        )
        conn.commit()
    return f"Linked deal {deal_id} to Gmail thread {thread_id}"


def add_touchpoint(
    deal_id: int,
    kind: str,
    summary: str,
    source_ref: str | None = None,
    occurred_at_iso: str | None = None,
) -> int:
    init_db()
    occ = occurred_at_iso or _utc_now()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO touchpoints (deal_id, kind, summary, source_ref, occurred_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (deal_id, kind.strip(), summary.strip(), source_ref, occ),
        )
        conn.execute("UPDATE deals SET updated_at = ? WHERE id = ?", (_utc_now(), deal_id))
        conn.commit()
        return int(cur.lastrowid)


def get_deal_by_thread(rep_name: str, thread_id: str) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM deals
            WHERE rep_name = ? COLLATE NOCASE AND gmail_thread_id = ?
            """,
            (rep_name.strip(), thread_id.strip()),
        ).fetchone()
        if not row:
            return None
        return _deal_bundle(conn, dict(row))


def get_deal_context(deal_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
        if not row:
            return None
        return _deal_bundle(conn, dict(row))


def list_active_deals(rep_name: str, limit: int = 20) -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM deals WHERE rep_name = ? COLLATE NOCASE
            ORDER BY updated_at DESC LIMIT ?
            """,
            (rep_name.strip(), limit),
        ).fetchall()
        return [_deal_bundle(conn, dict(r)) for r in rows]


def update_deal_stage(deal_id: int, stage: str) -> str:
    init_db()
    now = _utc_now()
    with _connect() as conn:
        conn.execute(
            "UPDATE deals SET stage = ?, updated_at = ? WHERE id = ?",
            (stage.strip(), now, deal_id),
        )
        conn.commit()
    return f"Deal {deal_id} stage -> {stage}"


def find_deal_by_account(rep_name: str, account_name: str) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM deals WHERE rep_name = ? COLLATE NOCASE AND account_name = ? COLLATE NOCASE
            """,
            (rep_name.strip(), account_name.strip()),
        ).fetchone()
        if not row:
            return None
        return _deal_bundle(conn, dict(row))


def _deal_bundle(conn: sqlite3.Connection, deal: dict) -> dict:
    did = deal["id"]
    touches = conn.execute(
        """
        SELECT id, kind, summary, source_ref, occurred_at FROM touchpoints
        WHERE deal_id = ? ORDER BY occurred_at DESC LIMIT 50
        """,
        (did,),
    ).fetchall()
    deal_out = dict(deal)
    if deal_out.get("value_cents") is not None:
        deal_out["value_dollars"] = deal_out["value_cents"] / 100.0
    deal_out["touchpoints"] = [dict(t) for t in touches]
    return deal_out


def deal_bundle_to_json(deal: dict) -> str:
    return json.dumps(deal, indent=2, default=str)


init_db()
