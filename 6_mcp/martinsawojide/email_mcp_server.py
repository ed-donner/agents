"""MCP server exposing SendGrid email (stdio). Launched via uv run from repo root."""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To

load_dotenv(override=True)

mcp = FastMCP("email_server")


@mcp.tool()
def send_email(subject: str, html_body: str) -> str:
    """Send an email with the given subject and HTML body using SendGrid.

    Args:
        subject: Email subject line.
        html_body: HTML content for the email body.
    """
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return "Error: SENDGRID_API_KEY is not set."

    from_email_addr = os.getenv("SENDGRID_FROM_EMAIL", "awojidemartins@gmail.com")
    to_email_addr = os.getenv("SENDGRID_TO_EMAIL", "awojidemartins@gmail.com")

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email(from_email_addr)
    to_email = To(to_email_addr)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return f"success (status {response.status_code})"


if __name__ == "__main__":
    mcp.run(transport="stdio")
