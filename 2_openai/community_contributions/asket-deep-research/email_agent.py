import contextvars
import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool

from config import EMAIL_MODEL_SETTINGS

# Set by ResearchManager before Runner.run(email_agent, ...) when the UI provides a recipient.
recipient_override: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "recipient_override", default=None
)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_addr = os.environ.get("SENDGRID_FROM")
    override = recipient_override.get()
    to_addr = (override.strip() if override else None) or os.environ.get("SENDGRID_TO")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY is not set")
    if not from_addr:
        raise RuntimeError("SENDGRID_FROM is not set")
    if not to_addr:
        raise RuntimeError("No recipient: enter your email in the app or set SENDGRID_TO")
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email(from_addr)
    to_email = To(to_addr)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        body = getattr(response, "body", None) or b""
        text = body.decode("utf-8", errors="replace") if isinstance(body, (bytes, bytearray)) else str(body)
        raise RuntimeError(f"SendGrid error {status}: {text[:500]}")
    return {"status": "success"}


INSTRUCTIONS = (
    "You are able to send a nicely formatted HTML email based on a detailed report. "
    "You will be provided with a detailed report. You should use your tool to send one email, "
    "providing the report converted into clean, well presented HTML with an appropriate subject line."
)

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    model_settings=EMAIL_MODEL_SETTINGS,
)
