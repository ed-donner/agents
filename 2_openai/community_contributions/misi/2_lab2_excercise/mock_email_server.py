from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).with_name("mock_email_server.sqlite3")


class MockEmailServer:
    """A tiny SQLite-backed mailbox service for local agent experiments."""

    def __init__(self, db_path: str | Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._initialize()

    def send_email(
        self,
        sender_email: str,
        recipient_email: str,
        subject: str,
        body: str,
    ) -> dict[str, Any]:
        self._validate_email(sender_email)
        self._validate_email(recipient_email)
        subject = subject.strip()
        body = body.strip()
        if not subject:
            raise ValueError("subject must not be empty")
        if not body:
            raise ValueError("body must not be empty")

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO emails (
                    thread_id,
                    sender_email,
                    recipient_email,
                    subject,
                    body,
                    is_read,
                    created_at
                )
                VALUES (NULL, ?, ?, ?, ?, 0, ?)
                """,
                (sender_email, recipient_email, subject, body, self._now()),
            )
            email_id = cursor.lastrowid
            conn.execute(
                "UPDATE emails SET thread_id = ? WHERE id = ?",
                (email_id, email_id),
            )

        return self.get_email(email_id)

    def read_emails(
        self,
        email_address: str,
        *,
        unread_only: bool = False,
        mark_as_read: bool = True,
    ) -> list[dict[str, Any]]:
        self._validate_email(email_address)
        where = "recipient_email = ?"
        params: list[Any] = [email_address]
        if unread_only:
            where += " AND is_read = 0"

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, thread_id, sender_email, recipient_email, subject, body, is_read, created_at
                FROM emails
                WHERE {where}
                ORDER BY created_at ASC, id ASC
                """,
                params,
            ).fetchall()

            if mark_as_read and rows:
                conn.executemany(
                    "UPDATE emails SET is_read = 1 WHERE id = ?",
                    [(row["id"],) for row in rows],
                )
                rows = conn.execute(
                    f"""
                    SELECT id, thread_id, sender_email, recipient_email, subject, body, is_read, created_at
                    FROM emails
                    WHERE {where}
                    ORDER BY created_at ASC, id ASC
                    """,
                    params,
                ).fetchall()

        return [dict(row) for row in rows]

    def reply_to_email(self, email_id: int, sender_email: str, body: str) -> dict[str, Any]:
        self._validate_email(sender_email)
        body = body.strip()
        if not body:
            raise ValueError("body must not be empty")

        original = self.get_email(email_id)

        if original["sender_email"] == sender_email:
            recipient_email = original["recipient_email"]
        elif original["recipient_email"] == sender_email:
            recipient_email = original["sender_email"]
        else:
            raise ValueError("sender_email must belong to the thread participants")

        subject = self._reply_subject(original["subject"])
        full_body = self._compose_reply_body(original["thread_id"], body)

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO emails (
                    thread_id,
                    sender_email,
                    recipient_email,
                    subject,
                    body,
                    is_read,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    original["thread_id"],
                    sender_email,
                    recipient_email,
                    subject,
                    full_body,
                    self._now(),
                ),
            )
            reply_id = cursor.lastrowid

        return self.get_email(reply_id)

    def forward_email(
        self,
        email_id: int,
        sender_email: str,
        recipient_email: str,
    ) -> dict[str, Any]:
        self._validate_email(sender_email)
        self._validate_email(recipient_email)

        original = self.get_email(email_id)
        subject = self._forward_subject(original["subject"])
        body = original["body"]

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO emails (
                    thread_id,
                    sender_email,
                    recipient_email,
                    subject,
                    body,
                    is_read,
                    created_at
                )
                VALUES (NULL, ?, ?, ?, ?, 0, ?)
                """,
                (sender_email, recipient_email, subject, body, self._now()),
            )
            forwarded_email_id = cursor.lastrowid
            conn.execute(
                "UPDATE emails SET thread_id = ? WHERE id = ?",
                (forwarded_email_id, forwarded_email_id),
            )

        return self.get_email(forwarded_email_id)

    def get_email(self, email_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, thread_id, sender_email, recipient_email, subject, body, is_read, created_at
                FROM emails
                WHERE id = ?
                """,
                (email_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"email with id={email_id} does not exist")
        return dict(row)

    def mark_as_read(self, email_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            updated = conn.execute(
                "UPDATE emails SET is_read = 1 WHERE id = ?",
                (email_id,),
            ).rowcount
        if updated == 0:
            raise ValueError(f"email with id={email_id} does not exist")
        return self.get_email(email_id)

    def get_thread(self, thread_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, thread_id, sender_email, recipient_email, subject, body, is_read, created_at
                FROM emails
                WHERE thread_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (thread_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def reset(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM emails")

    def _compose_reply_body(self, thread_id: int, new_body: str) -> str:
        history_lines = []
        for email in self.get_thread(thread_id):
            history_lines.append(
                "\n".join(
                    [
                        f"On {email['created_at']}, {email['sender_email']} wrote:",
                        self._indent_body(email["body"]),
                    ]
                )
            )
        history = "\n\n".join(reversed(history_lines))
        return f"{new_body}\n\n--- Original Message ---\n{history}" if history else new_body

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER,
                    sender_email TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _validate_email(email_address: str) -> None:
        if "@" not in email_address or email_address.startswith("@") or email_address.endswith("@"):
            raise ValueError(f"invalid email address: {email_address}")

    @staticmethod
    def _reply_subject(subject: str) -> str:
        return subject if subject.lower().startswith("re:") else f"Re: {subject}"

    @staticmethod
    def _forward_subject(subject: str) -> str:
        return subject if subject.lower().startswith("fwd:") else f"Fwd: {subject}"

    @staticmethod
    def _indent_body(body: str) -> str:
        return "\n".join(f"> {line}" for line in body.splitlines() or [""])

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


_DEFAULT_SERVER = MockEmailServer()


def send_email(
    sender_email: str,
    recipient_email: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    return _DEFAULT_SERVER.send_email(sender_email, recipient_email, subject, body)


def read_emails(
    email_address: str,
    *,
    unread_only: bool = False,
    mark_as_read: bool = True,
) -> list[dict[str, Any]]:
    return _DEFAULT_SERVER.read_emails(
        email_address,
        unread_only=unread_only,
        mark_as_read=mark_as_read,
    )


def reply_to_email(email_id: int, sender_email: str, body: str) -> dict[str, Any]:
    return _DEFAULT_SERVER.reply_to_email(email_id, sender_email, body)


def forward_email(email_id: int, sender_email: str, recipient_email: str) -> dict[str, Any]:
    return _DEFAULT_SERVER.forward_email(email_id, sender_email, recipient_email)


def get_email(email_id: int) -> dict[str, Any]:
    return _DEFAULT_SERVER.get_email(email_id)


def get_thread(thread_id: int) -> list[dict[str, Any]]:
    return _DEFAULT_SERVER.get_thread(thread_id)


def mark_as_read(email_id: int) -> dict[str, Any]:
    return _DEFAULT_SERVER.mark_as_read(email_id)


def reset_mailbox() -> None:
    _DEFAULT_SERVER.reset()
