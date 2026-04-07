import os
from typing import Any

import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> dict[str, Any]:
    """Send HTML email via SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "SENDGRID_API_KEY not set"}
    from_addr = os.environ.get("SENDGRID_FROM_EMAIL", "")
    to_addr = os.environ.get("SENDGRID_TO_EMAIL", "")
    if not from_addr or not to_addr:
        return {"status": "skipped", "reason": "SENDGRID_FROM_EMAIL or SENDGRID_TO_EMAIL not set"}
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email(from_addr)
    to_email = To(to_addr)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return {"status": "sent", "code": response.status_code}


INSTRUCTIONS = """Convert the report to clean HTML and send one email with a clear subject line
using your tool. If the tool reports skipped, respond with a short note that email was not configured."""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
