"""Mailtrap delivery for the Gradio apply workflow (opportunities_core).

**Recommended on Windows (avoids SMTP/fileno issues):** Email Sandbox HTTP API
  - MAILTRAP_API_KEY = API token from https://mailtrap.io/api-tokens
  - MAILTRAP_INBOX_ID = numeric inbox id from inbox URL (e.g. .../inboxes/2564102/...)
  - MAILTRAP_USE_SANDBOX = true (default)

**Alternative:** SMTP (MAILTRAP_USER, MAILTRAP_PASSWORD, ...). On Windows this runs in a
child process via `python mailtrap_smtp.py <payload.json>` when HTTP is not configured.

Payload JSON keys for CLI: to_addr, subject, body, from_addr.
"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import sys
import urllib.error
import urllib.request
from email.mime.text import MIMEText

MAILTRAP_DEFAULT_HOST = "sandbox.smtp.mailtrap.io"
MAILTRAP_DEFAULT_PORT = 2525


def mailtrap_config_from_env() -> dict | None:
    user = (os.getenv("MAILTRAP_USER") or os.getenv("SMTP_USER") or "").strip()
    password = (os.getenv("MAILTRAP_PASSWORD") or os.getenv("SMTP_PASSWORD") or "").strip()
    if not user or not password:
        return None
    host = (
        os.getenv("MAILTRAP_HOST") or os.getenv("SMTP_HOST") or MAILTRAP_DEFAULT_HOST
    ).strip()
    port = int(
        (
            os.getenv("MAILTRAP_PORT")
            or os.getenv("SMTP_PORT")
            or str(MAILTRAP_DEFAULT_PORT)
        ).strip()
        or str(MAILTRAP_DEFAULT_PORT)
    )
    if "mailtrap" not in host.lower():
        return None
    use_ssl = (os.getenv("SMTP_USE_SSL") or "").strip().lower() in ("1", "true", "yes")
    starttls_raw = (os.getenv("SMTP_STARTTLS") or "1").strip().lower()
    use_starttls = starttls_raw not in ("0", "false", "no")
    if use_ssl:
        use_starttls = False
    timeout_raw = (os.getenv("SMTP_TIMEOUT") or "90").strip() or "90"
    try:
        timeout_sec = max(10, int(timeout_raw))
    except ValueError:
        timeout_sec = 90
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "login_user": user,
        "use_ssl": use_ssl,
        "use_starttls": use_starttls,
        "timeout_sec": timeout_sec,
    }


def mailtrap_api_token_from_env() -> str:
    return (os.getenv("MAILTRAP_API_KEY") or os.getenv("MAILTRAP_API_TOKEN") or "").strip()


def mailtrap_http_send_configured() -> bool:
    """True if we can send via HTTPS (Sandbox or transactional API) without SMTP."""
    token = mailtrap_api_token_from_env()
    if not token:
        return False
    use_sandbox = (os.getenv("MAILTRAP_USE_SANDBOX") or "true").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    if use_sandbox:
        return bool((os.getenv("MAILTRAP_INBOX_ID") or "").strip())
    return True


def send_mailtrap_http_sync(
    to_addr: str,
    subject: str,
    body: str,
    from_addr: str,
    *,
    timeout_sec: float = 90.0,
) -> None:
    """
    POST to Mailtrap Email API (HTTPS). Sandbox: sandbox.api.mailtrap.io/api/send/{inbox_id}.
    Uses stdlib urllib only (no extra deps).
    """
    token = mailtrap_api_token_from_env()
    if not token:
        raise RuntimeError("MAILTRAP_API_KEY (or MAILTRAP_API_TOKEN) is not set")
    use_sandbox = (os.getenv("MAILTRAP_USE_SANDBOX") or "true").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    inbox_id = (os.getenv("MAILTRAP_INBOX_ID") or "").strip()
    if use_sandbox:
        if not inbox_id:
            raise RuntimeError("MAILTRAP_INBOX_ID is required for sandbox HTTP send")
        url = f"https://sandbox.api.mailtrap.io/api/send/{inbox_id}"
    else:
        url = "https://send.api.mailtrap.io/api/send"

    from_block: dict = {"email": from_addr.strip()}
    fn = (os.getenv("MAILTRAP_FROM_NAME") or "").strip()
    if fn:
        from_block["name"] = fn

    payload = {
        "from": from_block,
        "to": [{"email": to_addr.strip()}],
        "subject": subject,
        "text": body,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Mailtrap HTTP {e.code}: {detail}") from e


def send_mailtrap_deliver_sync(
    to_addr: str,
    subject: str,
    body: str,
    from_addr: str,
) -> None:
    """HTTP if configured, else SMTP (same process — use from subprocess on Windows for SMTP)."""
    if mailtrap_http_send_configured():
        send_mailtrap_http_sync(to_addr, subject, body, from_addr)
        return
    cfg = mailtrap_config_from_env()
    if not cfg:
        raise RuntimeError(
            "Mailtrap not configured: add MAILTRAP_API_KEY + MAILTRAP_INBOX_ID for sandbox HTTP, "
            "or MAILTRAP_USER + MAILTRAP_PASSWORD for SMTP."
        )
    send_mailtrap_email_sync(
        to_addr,
        subject,
        body,
        login_user=cfg["login_user"],
        from_addr=from_addr,
        password=cfg["password"],
        host=cfg["host"],
        port=cfg["port"],
        use_ssl=cfg["use_ssl"],
        use_starttls=cfg["use_starttls"],
        timeout_sec=cfg["timeout_sec"],
    )


def mailtrap_from_addr(applicant_email: str) -> str:
    env_from = (os.getenv("SMTP_FROM") or os.getenv("MAIL_FROM") or "").strip()
    if env_from:
        return env_from
    em = (applicant_email or "").strip()
    if em and "@" in em:
        return em
    return "applicant@example.com"


def send_mailtrap_email_sync(
    to_addr: str,
    subject: str,
    body: str,
    *,
    login_user: str,
    from_addr: str,
    password: str,
    host: str,
    port: int,
    use_ssl: bool = False,
    use_starttls: bool = True,
    timeout_sec: int = 90,
) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    ctx = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=timeout_sec, context=ctx) as smtp:
            smtp.ehlo()
            smtp.login(login_user, password)
            smtp.sendmail(from_addr, [to_addr], msg.as_string())
        return
    with smtplib.SMTP(host, port, timeout=timeout_sec) as smtp:
        smtp.ehlo()
        if use_starttls:
            smtp.starttls(context=ctx)
            smtp.ehlo()
        smtp.login(login_user, password)
        smtp.sendmail(from_addr, [to_addr], msg.as_string())


def send_from_payload_json_path(payload_path: str) -> int:
    """Used by child process: read JSON file and send one message."""
    from pathlib import Path

    data = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if not mailtrap_http_send_configured() and not mailtrap_config_from_env():
        print("Mailtrap not configured in environment", file=sys.stderr)
        return 2
    try:
        send_mailtrap_deliver_sync(
            data["to_addr"],
            data["subject"],
            data["body"],
            data["from_addr"],
        )
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python mailtrap_smtp.py <payload.json>", file=sys.stderr)
        sys.exit(1)
    sys.exit(send_from_payload_json_path(sys.argv[1]))
