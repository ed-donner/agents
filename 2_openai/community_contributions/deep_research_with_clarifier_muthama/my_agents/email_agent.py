from __future__ import annotations

import os
import logging
import re
import sendgrid
from typing import Dict, Optional, List, TypedDict
from sendgrid.helpers.mail import Mail, Content, From, To, Personalization
from agents import Agent, function_tool

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type



logger = logging.getLogger("email_agent")
logger.addHandler(logging.NullHandler())

SENDGRID_API_KEY_ENV = "SENDGRID_API_KEY"
DEFAULT_FROM_ENV = "DEFAULT_EMAIL_FROM"
DEFAULT_TO_ENV = "DEFAULT_EMAIL_TO"

MAX_SUBJECT_LENGTH = 200
MAX_BODY_BYTES = 2 * 1024 * 1024

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""


class EmailResult(TypedDict):
    status: str
    status_code: Optional[int]
    sg_response_body: Optional[Dict]
    message: Optional[str]


class EmailError(Exception):
    """Base class for email errors."""


class ConfigurationError(EmailError):
    pass


class ValidationError(EmailError):
    pass


class SendGridError(EmailError):
    pass


def _sanitize_html(html: str) -> str:
    """
    Sanitize HTML using bleach if available; otherwise do a conservative sanitize by stripping
    dangerous tags/attributes. This prevents script/style injection and similar issues.
    """
    if not html:
        return ""

    cleaned = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    cleaned = re.sub(r'on\w+="[^"]*"', "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"javascript:", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _get_sendgrid_client() -> "sendgrid.SendGridAPIClient":
    api_key = os.environ.get(SENDGRID_API_KEY_ENV)
    if not api_key:
        raise ConfigurationError(f"required environment variable {SENDGRID_API_KEY_ENV} not found")
    if sendgrid is None:
        raise ConfigurationError("sendgrid package is not installed or failed to import")
    return sendgrid.SendGridAPIClient(api_key=api_key)


def _validate_addresses(addr: Optional[str]) -> Optional[str]:
    if addr is None:
        return None
    addr = addr.strip()
    if not addr:
        return None
    # Very light validation — do not do complex regex here; let mail service reject truly invalid addresses.
    if "@" not in addr or len(addr) < 5:
        raise ValidationError(f"invalid email address: {addr!r}")
    return addr


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
    retry=retry_if_exception_type(SendGridError),
)
def _send_via_sendgrid(subject: str, html_body: str, from_email: str, to_emails: List[str]) -> Dict:
    """
    Low-level send via SendGrid. Retries for transient 5xx responses or network problems.
    Raises SendGridError on permanent failure.
    """
    client = _get_sendgrid_client()

    mail = Mail()
    mail.from_email = From(from_email)
    mail.subject = subject
    # build Personalization for multiple recipients
    personalization = Personalization()
    for to in to_emails:
        personalization.add_to(To(to))
    mail.add_personalization(personalization)
    mail.add_content(Content("text/html", html_body))

    logger.debug("Sending email via SendGrid", extra={"from": from_email, "tos": to_emails, "subject_len": len(subject)})
    response = client.client.mail.send.post(request_body=mail.get())
    status_code = getattr(response, "status_code", None)
    body = None
    try:
        # response.body may be bytes
        raw_body = getattr(response, "body", None)
        if raw_body:
            import json

            if isinstance(raw_body, (bytes, bytearray)):
                body = json.loads(raw_body.decode("utf-8", errors="ignore"))
            elif isinstance(raw_body, str):
                body = json.loads(raw_body)
            else:
                body = raw_body
    except Exception:
        body = {"raw": str(raw_body)}

    # Retry on transient server errors (5xx)
    if status_code is None:
        raise SendGridError("no status code returned from SendGrid client")
    if 500 <= status_code < 600:
        logger.warning("SendGrid returned transient error; will retry", extra={"status_code": status_code})
        raise SendGridError(f"sendgrid transient error: {status_code}")

    if status_code >= 400:
        # permanent failure
        raise SendGridError(f"sendgrid error {status_code}: {body}")

    return {"status_code": status_code, "body": body}


@function_tool
def send_email(subject: str, html_body: str, from_email: Optional[str] = None, to_email: Optional[str] = None) -> EmailResult:
    """
    Send an HTML email using SendGrid.
    - subject: subject line (max length enforced)
    - html_body: HTML content (sanitized)
    - from_email: optional override for the sender; otherwise uses env DEFAULT_FROM_ENV
    - to_email: optional recipient override; otherwise uses env DEFAULT_TO_ENV (can be comma-separated)
    Returns EmailResult typed dict.
    """
    # Normalize and validate addresses from env or args
    from_addr = from_email or os.environ.get(DEFAULT_FROM_ENV)
    to_addr = to_email or os.environ.get(DEFAULT_TO_ENV)

    from_addr = _validate_addresses(from_addr)
    to_addr = _validate_addresses(to_addr)

    if not to_addr:
        raise ValidationError("recipient email not provided (to_email param or DEFAULT_EMAIL_TO env var required)")

    if not from_addr:
        raise ValidationError("sender email not provided (from_email param or DEFAULT_EMAIL_FROM env var required)")

    # Basic subject validation
    subject = (subject or "").strip()
    if not subject:
        raise ValidationError("subject must be a non-empty string")
    if len(subject) > MAX_SUBJECT_LENGTH:
        raise ValidationError(f"subject too long (max {MAX_SUBJECT_LENGTH} chars)")

    # Body size guard
    if not html_body or not html_body.strip():
        raise ValidationError("html_body must be provided and non-empty")
    if len(html_body.encode("utf-8")) > MAX_BODY_BYTES:
        raise ValidationError(f"html_body exceeds maximum size of {MAX_BODY_BYTES} bytes")

    # sanitize
    cleaned_html = _sanitize_html(html_body)

    # recipients support comma-separated addresses
    recipients = [recipient.strip() for recipient in to_addr.split(",") if recipient.strip()]

    try:
        send_result = _send_via_sendgrid(subject=subject, html_body=cleaned_html, from_email=from_addr, to_emails=recipients)
        return {"status": "ok", "status_code": send_result.get("status_code"), "sg_response_body": send_result.get("body"), "message": None}
    except SendGridError as error:
        logger.exception("send_email:sendgrid_error")
        return {"status": "error", "status_code": None, "sg_response_body": None, "message": str(error)}
    except ConfigurationError as error:
        logger.exception("send_email:config_error")
        return {"status": "error", "status_code": None, "sg_response_body": None, "message": str(error)}
    except ValidationError as error:
        logger.exception("send_email:validation_error")
        return {"status": "error", "status_code": None, "sg_response_body": None, "message": str(error)}
    except Exception as error:
        logger.exception("send_email:unexpected_error")
        return {"status": "error", "status_code": None, "sg_response_body": None, "message": f"unexpected error: {error}"}


email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
