from __future__ import annotations

import logging
import re
import smtplib
from email.message import EmailMessage
from typing import Any, List

from education_coach.config import get_settings

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_MAX_BODY_CHARS = 100_000
_SUBJECT = "Education Sidekick — your conversation summary"


def is_valid_recipient(email: str) -> bool:
    s = (email or "").strip()
    return bool(s and _EMAIL_RE.match(s))


def sendgrid_ready() -> bool:
    s = get_settings()
    return bool(
        (s.sendgrid_api_key or "").strip() and (s.sendgrid_from_email or "").strip()
    )


def smtp_ready() -> bool:
    s = get_settings()
    from_addr = s.smtp_from or s.smtp_user
    return bool(s.smtp_host and from_addr)


def email_ready() -> bool:
    return sendgrid_ready() or smtp_ready()


def format_chat_plain(history: List[Any], *, include_evaluator: bool = False) -> str:
    lines: List[str] = []
    for m in history or []:
        if not isinstance(m, dict):
            continue
        role = m.get("role", "")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if not include_evaluator and role == "assistant" and content.startswith("Evaluator:"):
            continue
        label = {"user": "Student", "assistant": "Tutor"}.get(role, role.capitalize())
        lines.append(f"{label}:\n{content}\n")
    return "\n".join(lines)


def _build_plain_body(history: List[Any]) -> str:
    body = format_chat_plain(history)
    if not body.strip():
        raise ValueError("Nothing to send — the conversation is empty.")
    if len(body) > _MAX_BODY_CHARS:
        body = body[:_MAX_BODY_CHARS] + "\n\n[... truncated for email size ...]"
    return (
        "Below is a copy of your session from Education Sidekick.\n\n"
        "---\n\n"
        f"{body}\n\n"
        "---\n"
        "This message was sent automatically. Please do not reply to it.\n"
    )


def _send_via_sendgrid(*, to_addr: str, plain_body: str) -> None:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Content, Email, Mail, To

    settings = get_settings()
    key = (settings.sendgrid_api_key or "").strip()
    from_email = (settings.sendgrid_from_email or "").strip()
    message = Mail(
        from_email=Email(from_email),
        to_emails=To(to_addr.strip()),
        subject=_SUBJECT,
        plain_text_content=Content("text/plain", plain_body),
    )
    client = SendGridAPIClient(key)
    response = client.send(message)
    code = getattr(response, "status_code", None)
    if code is not None and code not in (200, 202):
        body = getattr(response, "body", b"") or b""
        try:
            detail = body.decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = str(body)[:500]
        raise RuntimeError(f"SendGrid HTTP {code}: {detail}")


def _send_via_smtp(*, to_addr: str, plain_body: str) -> None:
    settings = get_settings()
    if not smtp_ready():
        raise RuntimeError("SMTP is not configured.")

    from_addr = (settings.smtp_from or settings.smtp_user or "").strip()
    msg = EmailMessage()
    msg["Subject"] = _SUBJECT
    msg["From"] = from_addr
    msg["To"] = to_addr.strip()
    msg.set_content(plain_body, subtype="plain", charset="utf-8")

    host = settings.smtp_host or ""
    port = int(settings.smtp_port or 587)
    user = settings.smtp_user
    password = settings.smtp_password

    logger.info("Sending email to %s via SMTP %s:%s", to_addr.strip(), host, port)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=45) as smtp:
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=45) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)


def send_conversation_to_student(*, to_email: str, history: List[Any]) -> None:
    if not is_valid_recipient(to_email):
        raise ValueError("Invalid email address.")
    if not email_ready():
        raise RuntimeError(
            "Email is not configured. Set SENDGRID_API_KEY + SENDGRID_FROM_EMAIL (SendGrid), "
            "or SMTP_HOST + From + credentials (SMTP). See README."
        )

    body = _build_plain_body(history)
    to_addr = to_email.strip()

    if sendgrid_ready():
        logger.info("Sending email to %s via SendGrid", to_addr)
        _send_via_sendgrid(to_addr=to_addr, plain_body=body)
    else:
        _send_via_smtp(to_addr=to_addr, plain_body=body)
