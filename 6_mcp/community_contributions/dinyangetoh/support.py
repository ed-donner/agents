import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

_DB_PATH = Path(__file__).resolve().parent / "support.db"

VALID_STATUS = frozenset({"open", "escalated", "resolved"})
VALID_PRIORITY = frozenset({"low", "medium", "high"})
VALID_MESSAGE_ROLES = frozenset({"customer", "agent", "system"})

KNOWLEDGE_BASE: dict[str, str] = {
    "password_reset": (
        "Password reset: Go to Sign in > Forgot password, enter your email, "
        "and use the link within 15 minutes. If you do not see the email, check spam "
        "and verify the address on file. For security, previous sessions may be signed out."
    ),
    "billing": (
        "Billing: Invoices are available under Account > Billing history. "
        "Payment methods can be updated there. Refunds for duplicate charges are processed "
        "within 5–7 business days after support confirms the duplicate."
    ),
    "account_setup": (
        "Account setup: After signup, confirm your email, complete your profile, "
        "and enable two-factor authentication under Security. Team accounts can invite "
        "members from Organization > Members."
    ),
    "returns": (
        "Returns: Initiate a return from Orders > Request return within 30 days of delivery. "
        "Items must be unused with tags. You'll receive a prepaid label by email once approved."
    ),
    "shipping": (
        "Shipping: Standard delivery is 3–5 business days; express is 1–2. "
        "Tracking appears in Orders once the carrier scans the package. "
        "Contact us if tracking shows no movement for 5 days."
    ),
    "technical_issues": (
        "Technical issues: Clear cache and cookies, try an incognito window, and ensure "
        "your browser is up to date. If errors persist, note the exact error message and "
        "approximate time (with timezone) for engineering to trace logs."
    ),
}


class Ticket(BaseModel):
    ticket_id: str
    customer_name: str
    issue: str
    status: str
    priority: str
    notes: str = ""
    created_at: str
    resolved_at: str | None = None
    resolution: str | None = None


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            resolution TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id),
            role TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_created
        ON ticket_messages (ticket_id, created_at)
        """
    )
    conn.commit()


def _row_to_ticket(row: sqlite3.Row) -> Ticket:
    return Ticket(
        ticket_id=row["ticket_id"],
        customer_name=row["customer_name"],
        issue=row["issue"],
        status=row["status"],
        priority=row["priority"],
        notes=row["notes"] or "",
        created_at=row["created_at"],
        resolved_at=row["resolved_at"],
        resolution=row["resolution"],
    )


def create_ticket(customer_name: str, issue: str, priority: str) -> Ticket:
    p = priority.lower().strip()
    if p not in VALID_PRIORITY:
        raise ValueError(f"priority must be one of {sorted(VALID_PRIORITY)}")
    ticket_id = f"TKT-{uuid.uuid4().hex[:10]}"
    created = _now()
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO tickets (ticket_id, customer_name, issue, status, priority, notes, created_at)
            VALUES (?, ?, ?, 'open', ?, '', ?)
            """,
            (ticket_id, customer_name.strip(), issue.strip(), p, created),
        )
        conn.commit()
    return get_ticket(ticket_id)


def get_ticket(ticket_id: str) -> Ticket:
    with _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id.strip(),)
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"Unknown ticket_id: {ticket_id}")
    return _row_to_ticket(row)


def update_ticket(ticket_id: str, notes: str) -> str:
    t = get_ticket(ticket_id)
    if t.status == "resolved":
        raise ValueError("Cannot update notes on a resolved ticket.")
    extra = notes.strip()
    new_notes = f"{t.notes}\n{extra}".strip() if t.notes else extra
    with _conn() as conn:
        conn.execute(
            "UPDATE tickets SET notes = ? WHERE ticket_id = ?",
            (new_notes, t.ticket_id),
        )
        conn.commit()
    return f"Updated ticket {t.ticket_id} with new notes."


def escalate_ticket(ticket_id: str, reason: str) -> str:
    t = get_ticket(ticket_id)
    if t.status == "resolved":
        raise ValueError("Cannot escalate a resolved ticket.")
    r = reason.strip()
    line = f"[escalated {_now()}] {r}"
    new_notes = f"{t.notes}\n{line}".strip() if t.notes else line
    with _conn() as conn:
        conn.execute(
            "UPDATE tickets SET status = 'escalated', notes = ? WHERE ticket_id = ?",
            (new_notes, t.ticket_id),
        )
        conn.commit()
    return f"Ticket {t.ticket_id} escalated."


def close_ticket(ticket_id: str, resolution: str) -> str:
    t = get_ticket(ticket_id)
    res = resolution.strip()
    closed = _now()
    with _conn() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET status = 'resolved', resolution = ?, resolved_at = ?
            WHERE ticket_id = ?
            """,
            (res, closed, t.ticket_id),
        )
        conn.commit()
    return f"Ticket {t.ticket_id} resolved."


def append_ticket_message(ticket_id: str, role: str, body: str) -> str:
    r = role.lower().strip()
    if r not in VALID_MESSAGE_ROLES:
        raise ValueError(f"role must be one of {sorted(VALID_MESSAGE_ROLES)}")
    text = body.strip()
    if not text:
        raise ValueError("body must be non-empty")
    t = get_ticket(ticket_id)
    ts = _now()
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO ticket_messages (ticket_id, role, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (t.ticket_id, r, text, ts),
        )
        conn.commit()
    return f"Logged {r} message on ticket {t.ticket_id}."


def get_ticket_thread(ticket_id: str) -> str:
    t = get_ticket(ticket_id)
    header = ticket_summary(t)
    with _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute(
            """
            SELECT role, body, created_at
            FROM ticket_messages
            WHERE ticket_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (t.ticket_id,),
        )
        rows = cur.fetchall()
    if not rows:
        thread_section = (
            "\n\n--- Thread ---\n"
            "No thread messages yet. Use internal notes and resolution above for legacy context."
        )
    else:
        lines = ["\n\n--- Thread (oldest first) ---"]
        for row in rows:
            lines.append(f"[{row['created_at']}] {row['role']}: {row['body']}")
        thread_section = "\n".join(lines)
    if t.status == "resolved":
        thread_section += (
            "\n\n**This ticket is resolved.** For more help on the same issue, call reopen_ticket "
            "then continue; for a new unrelated issue, create_ticket and mention the prior ticket id in the issue text."
        )
    return header + thread_section


def get_ticket_messages(ticket_id: str) -> list[str]:
    with _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute(
            "SELECT role, body, created_at FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at ASC, id ASC",
            (ticket_id,),
        )
        rows = cur.fetchall()
        return [{"role": row["role"], "body": row["body"], "created_at": row["created_at"]} for row in rows]


def reopen_ticket(ticket_id: str, reason: str) -> str:
    t = get_ticket(ticket_id)
    if t.status != "resolved":
        raise ValueError(
            f"Ticket {t.ticket_id} is not resolved (status={t.status}); reopen is only for resolved tickets."
        )
    r = reason.strip()
    line = f"[reopened {_now()}] {r}"
    if t.resolution:
        line += f" | prior resolution: {t.resolution}"
    new_notes = f"{t.notes}\n{line}".strip() if t.notes else line
    with _conn() as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            UPDATE tickets
            SET status = 'open', notes = ?, resolved_at = NULL, resolution = NULL
            WHERE ticket_id = ?
            """,
            (new_notes, t.ticket_id),
        )
        conn.commit()
    return f"Ticket {t.ticket_id} reopened and is open for follow-up."


def search_kb(query: str) -> list[str]:
    q = query.lower().strip()
    if not q:
        return []
    tokens = [w for w in q.replace(",", " ").split() if w]
    hits: list[str] = []
    for topic, body in KNOWLEDGE_BASE.items():
        hay = f"{topic} {body}".lower()
        if any(tok in hay for tok in tokens) or q in hay:
            hits.append(topic)
    return sorted(set(hits))


def get_article(topic: str) -> str:
    key = topic.strip().lower().replace(" ", "_")
    if key not in KNOWLEDGE_BASE:
        return f"No article for topic '{topic}'. Known topics: {', '.join(sorted(KNOWLEDGE_BASE))}."
    return KNOWLEDGE_BASE[key]


def ticket_summary(t: Ticket) -> str:
    lines = [
        f"Ticket {t.ticket_id}",
        f"Customer: {t.customer_name}",
        f"Status: {t.status} | Priority: {t.priority}",
        f"Created: {t.created_at}",
        f"Issue: {t.issue}",
    ]
    if t.notes:
        lines.append(f"Notes:\n{t.notes}")
    if t.resolution:
        lines.append(f"Resolution: {t.resolution}")
    if t.resolved_at:
        lines.append(f"Resolved at: {t.resolved_at}")
    return "\n".join(lines)


if __name__ == "__main__":
    _DB_PATH.unlink(missing_ok=True)
    t1 = create_ticket(
        "Alex Example", "Cannot log in after password reset email", "high")
    print("Created:", t1.ticket_id)
    print(update_ticket(t1.ticket_id, "Customer verified email on file."))
    print(escalate_ticket(t1.ticket_id,
          "Suspected account lockout; needs identity check."))
    print(close_ticket(t1.ticket_id,
          "Verified identity; password reset completed successfully."))
    print("Final:", get_ticket(t1.ticket_id))
    print(append_ticket_message(t1.ticket_id, "agent",
          "Prior reply logged for thread demo."))
    print(get_ticket_thread(t1.ticket_id))
    print(reopen_ticket(t1.ticket_id, "Customer reported same symptom after closure."))
    print("After reopen:", get_ticket(t1.ticket_id).status)
    print("KB search 'password':", search_kb("password"))
