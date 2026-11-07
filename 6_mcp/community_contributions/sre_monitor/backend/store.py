import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from .settings import PROJECT_DIR
from .sources import RESOLVED_STATUSES, Incident, ServiceSnapshot

DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "monitor.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS services (
    name TEXT PRIMARY KEY, url TEXT, indicator TEXT, description TEXT,
    degraded_components TEXT, checked_at TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS incidents (
    key TEXT PRIMARY KEY, service TEXT, incident_id TEXT, name TEXT, status TEXT, impact TEXT,
    link TEXT, components TEXT, updates TEXT, created_at TEXT, updated_at TEXT, resolved_at TEXT,
    first_seen_at TEXT, is_incident INTEGER, summary TEXT, severity TEXT, global_impact INTEGER,
    priority INTEGER, triage_reason TEXT, notified_at TEXT, impact_corroborated INTEGER,
    verification_confidence TEXT, verification_summary TEXT, verification_sources TEXT
);
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, agent TEXT, kind TEXT, message TEXT
);
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, subject TEXT, recipients TEXT,
    priority INTEGER, sent INTEGER, error TEXT
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""

_initialised = False
INCIDENT_COLUMNS = {
    "impact_corroborated": "INTEGER",
    "verification_confidence": "TEXT",
    "verification_summary": "TEXT",
    "verification_sources": "TEXT",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds") if value else None


@contextmanager
def connect():
    global _initialised
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        if not _initialised:
            conn.executescript(SCHEMA)
            existing = {
                row["name"] for row in conn.execute("PRAGMA table_info(incidents)").fetchall()
            }
            for name, data_type in INCIDENT_COLUMNS.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE incidents ADD COLUMN {name} {data_type}")
            _initialised = True
        yield conn
        conn.commit()
    finally:
        conn.close()


def _incident_row(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["components"] = json.loads(data["components"] or "[]")
    data["updates"] = json.loads(data["updates"] or "[]")
    data["verification_sources"] = json.loads(data.get("verification_sources") or "[]")
    for flag in ("is_incident", "global_impact", "priority", "impact_corroborated"):
        data[flag] = None if data[flag] is None else bool(data[flag])
    return data


def save_service(snapshot: ServiceSnapshot) -> str | None:
    """Store the latest status of a service and return its previous error, if any."""
    with connect() as conn:
        previous = conn.execute("SELECT error FROM services WHERE name = ?", (snapshot.service,)).fetchone()
        conn.execute(
            """INSERT INTO services (name, url, indicator, description, degraded_components, checked_at, error)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET url = excluded.url, indicator = excluded.indicator,
                 description = excluded.description, degraded_components = excluded.degraded_components,
                 checked_at = excluded.checked_at, error = excluded.error""",
            (
                snapshot.service,
                snapshot.url,
                snapshot.indicator,
                snapshot.description,
                json.dumps(snapshot.degraded_components),
                iso(utcnow()),
                snapshot.error,
            ),
        )
    return previous["error"] if previous else None


def prune_services(names: list[str]) -> None:
    """Forget services that are no longer in config.yaml, so the dashboard and postmortems only cover the current list."""
    if not names:
        return
    placeholders = ",".join("?" for _ in names)
    with connect() as conn:
        conn.execute(f"DELETE FROM incidents WHERE service NOT IN ({placeholders})", names)
        conn.execute(f"DELETE FROM services WHERE name NOT IN ({placeholders})", names)


def services() -> dict[str, dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM services").fetchall()
    result = {}
    for row in rows:
        data = dict(row)
        data["degraded_components"] = json.loads(data["degraded_components"] or "[]")
        result[data["name"]] = data
    return result


def upsert_incident(incident: Incident) -> dict | None:
    """Insert or refresh an incident and return the stored version from before this call."""
    with connect() as conn:
        previous = conn.execute("SELECT * FROM incidents WHERE key = ?", (incident.key,)).fetchone()
        values = (
            incident.name,
            incident.status,
            incident.impact,
            incident.link,
            json.dumps(incident.components),
            json.dumps(incident.updates),
            iso(incident.updated_at),
            iso(incident.resolved_at),
        )
        if previous is None:
            conn.execute(
                """INSERT INTO incidents (name, status, impact, link, components, updates, updated_at,
                     resolved_at, key, service, incident_id, created_at, first_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values
                + (incident.key, incident.service, incident.incident_id, iso(incident.created_at), iso(utcnow())),
            )
        else:
            conn.execute(
                """UPDATE incidents SET name = ?, status = ?, impact = ?, link = ?, components = ?,
                     updates = ?, updated_at = ?, resolved_at = ? WHERE key = ?""",
                values + (incident.key,),
            )
    return _incident_row(previous) if previous else None


def save_watch_reports(reports: list[dict]) -> None:
    with connect() as conn:
        conn.executemany(
            "UPDATE incidents SET is_incident = ?, summary = ? WHERE key = ?",
            [(int(report["is_service_incident"]), report["summary"], report["key"]) for report in reports],
        )


def save_triage(decisions: list[dict]) -> None:
    with connect() as conn:
        conn.executemany(
            """UPDATE incidents SET severity = ?, global_impact = ?, priority = ?, triage_reason = ?
               WHERE key = ?""",
            [
                (d["severity"], int(d["global_impact"]), int(d["priority"]), d["rationale"], d["key"])
                for d in decisions
            ],
        )


def save_verifications(verifications: list[dict]) -> None:
    with connect() as conn:
        conn.executemany(
            """UPDATE incidents SET impact_corroborated = ?, verification_confidence = ?,
               verification_summary = ?, verification_sources = ? WHERE key = ?""",
            [
                (
                    int(item["corroborated"]),
                    item["confidence"],
                    item["summary"],
                    json.dumps(item["sources"]),
                    item["key"],
                )
                for item in verifications
            ],
        )


def mark_notified(keys: list[str]) -> None:
    with connect() as conn:
        conn.executemany(
            "UPDATE incidents SET notified_at = ? WHERE key = ?", [(iso(utcnow()), key) for key in keys]
        )


def incidents_since(hours: float) -> list[dict]:
    cutoff = iso(utcnow() - timedelta(hours=hours))
    with connect() as conn:
        rows = conn.execute(
            """SELECT * FROM incidents WHERE created_at >= ? AND COALESCE(is_incident, 1) = 1
               ORDER BY created_at DESC""",
            (cutoff,),
        ).fetchall()
    return [_incident_row(row) for row in rows]


def active_incidents(max_age_days: int = 7) -> list[dict]:
    cutoff = iso(utcnow() - timedelta(days=max_age_days))
    placeholders = ",".join("?" for _ in RESOLVED_STATUSES)
    with connect() as conn:
        rows = conn.execute(
            f"""SELECT * FROM incidents WHERE status NOT IN ({placeholders}) AND created_at >= ?
                AND COALESCE(is_incident, 1) = 1
                ORDER BY COALESCE(priority, 0) DESC, created_at DESC""",
            (*RESOLVED_STATUSES, cutoff),
        ).fetchall()
    return [_incident_row(row) for row in rows]


def log(agent: str, kind: str, message: str) -> None:
    print(f"[{agent}] {message}")
    with connect() as conn:
        conn.execute(
            "INSERT INTO activity (ts, agent, kind, message) VALUES (?, ?, ?, ?)",
            (iso(utcnow()), agent, kind, message),
        )


def recent_activity(limit: int = 100) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def record_email(kind: str, subject: str, recipients: list[str], priority: bool, sent: bool, error: str | None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO emails (ts, kind, subject, recipients, priority, sent, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (iso(utcnow()), kind, subject, ", ".join(recipients), int(priority), int(sent), error),
        )


def recent_emails(limit: int = 30) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM emails ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_meta(key: str) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
