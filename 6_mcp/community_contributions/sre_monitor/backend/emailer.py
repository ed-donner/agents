import os
import re
import smtplib
from email.message import EmailMessage

import httpx

from . import store
from .settings import get_settings, ssl_context

OUTBOX_DIR = store.DATA_DIR / "outbox"
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
PUSH_SEVERITIES = {"SEV1", "SEV2"}


def recipients(priority: bool = False) -> list[str]:
    email = get_settings().email
    default = email.recipients or [address for address in [os.getenv("EMAIL_ADDRESS")] if address]
    if priority:
        return list(dict.fromkeys(default + email.priority_recipients))
    return default


def send_email(
    kind: str,
    subject: str,
    html_body: str,
    text_body: str,
    to: list[str],
    priority: bool = False,
    attachments: list[tuple[str, bytes, str]] = (),
    dry_run: bool = False,
) -> bool:
    """Send an email over SMTP, or save it to data/outbox when dry_run is set. Returns True on success."""
    if dry_run:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")[:60]
        path = OUTBOX_DIR / f"{store.utcnow():%Y%m%d-%H%M%S}-{slug}.html"
        path.write_text(f"<!-- To: {', '.join(to)} | priority: {priority} -->\n<h2>{subject}</h2>\n{html_body}")
        store.record_email(kind, subject, to, priority, sent=False, error=f"dry run: saved to {path.name}")
        store.log("Notifier", "email", f"Dry run, saved '{subject}' to data/outbox/{path.name}")
        return True

    sender = os.getenv("EMAIL_ADDRESS")
    server = os.getenv("EMAIL_SMTP_SERVER")
    # Gmail displays app passwords in four groups. The course labs require storing
    # the same 16 characters without the display spaces; accept either form here.
    password = "".join(os.getenv("EMAIL_APP_PASSWORD", "").split())
    if not (sender and server and password and to):
        error = "EMAIL_ADDRESS, EMAIL_SMTP_SERVER, EMAIL_APP_PASSWORD and a recipient are required"
        store.record_email(kind, subject, to, priority, sent=False, error=error)
        store.log("Notifier", "error", f"Email not sent: {error}")
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(to)
    message["Subject"] = subject
    if priority:
        message["X-Priority"] = "1 (Highest)"
        message["X-MSMail-Priority"] = "High"
        message["Importance"] = "High"
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    for filename, data, mime_type in attachments:
        maintype, subtype = mime_type.split("/", 1)
        message.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    try:
        # Match the email setup used by the course labs.
        with smtplib.SMTP(server, 587) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(message)
    except Exception as exc:
        store.record_email(kind, subject, to, priority, sent=False, error=str(exc)[:300])
        store.log("Notifier", "error", f"Email '{subject}' failed: {exc}")
        return False
    store.record_email(kind, subject, to, priority, sent=True, error=None)
    store.log("Notifier", "email", f"Sent '{subject}' to {', '.join(to)}")
    return True


def send_push(title: str, message: str, url: str, severity: str, dry_run: bool = False) -> bool:
    """Push a SEV1 or SEV2 incident through Pushover. SEV1 is sent at high priority."""
    high = severity == "SEV1"
    if dry_run:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
        path = OUTBOX_DIR / f"{store.utcnow():%Y%m%d-%H%M%S}-push-{slug}.txt"
        path.write_text(f"{title}\n\n{message}\n\n{url}\n")
        store.record_email("push", title, ["pushover"], high, sent=False, error=f"dry run: saved to {path.name}")
        store.log("Notifier", "push", f"Dry run, saved push '{title}' to data/outbox/{path.name}")
        return True

    user, token = os.getenv("PUSHOVER_USER"), os.getenv("PUSHOVER_TOKEN")
    if not (user and token):
        error = "PUSHOVER_USER and PUSHOVER_TOKEN are required"
        store.record_email("push", title, ["pushover"], high, sent=False, error=error)
        store.log("Notifier", "error", f"Push not sent: {error}")
        return False
    try:
        response = httpx.post(
            PUSHOVER_URL,
            data={
                "user": user,
                "token": token,
                "title": title[:250],
                "message": message[:1024],
                "url": url[:512],
                "url_title": "View incident",
                "priority": 1 if high else 0,
            },
            verify=ssl_context(),
            timeout=30,
        )
        response.raise_for_status()
    except Exception as exc:
        store.record_email("push", title, ["pushover"], high, sent=False, error=str(exc)[:300])
        store.log("Notifier", "error", f"Push '{title}' failed: {exc}")
        return False
    store.record_email("push", title, ["pushover"], high, sent=True, error=None)
    store.log("Notifier", "push", f"Pushed '{title}'")
    return True
