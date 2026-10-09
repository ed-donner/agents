"""Gmail integration: read recent emails and draft replies."""

import base64
import email as email_lib
from typing import Any
from googleapiclient.discovery import build
from google_auth import get_google_credentials


def _gmail_service() -> Any:
    creds = get_google_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured. See README for setup.")
    return build("gmail", "v1", credentials=creds)


def get_recent_emails(max_results: int = 10) -> list[dict]:
    """Fetch recent inbox emails. Returns list of {id, subject, from, snippet, body}."""
    service = _gmail_service()
    result = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
        .execute()
    )
    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in detail["payload"].get("headers", [])}
        body = _extract_body(detail["payload"])
        emails.append(
            {
                "id": msg["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
                "body": body[:2000],  # cap to avoid token bloat
            }
        )
    return emails


def create_draft(to: str, subject: str, body: str) -> str:
    """Create a Gmail draft. Returns the draft ID."""
    service = _gmail_service()
    raw = _build_raw_message(to, subject, body)
    draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return draft["id"]


# ── helpers ──────────────────────────────────────────────────────────

def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


def _build_raw_message(to: str, subject: str, body: str) -> str:
    """Encode an email message as base64url for the Gmail API."""
    message = email_lib.message.EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    return base64.urlsafe_b64encode(message.as_bytes()).decode()
