import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail, To
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "olasogbayimika@gmail.com")
TO_EMAIL = os.getenv("SENDGRID_TO_EMAIL", "adebimpefolayemi1@gmail.com")

mcp = FastMCP("email_server")


class SendFinalOutputEmailArgs(BaseModel):
    body: str = Field(
        description="Plain-text body to email (e.g. research summary). "
        "Recipient is fixed by the server config, not a tool argument."
    )
    subject: str = Field(
        default="Research assistant output",
        description="Short subject line for the email.",
    )


@mcp.tool()
def send_final_output_email(args: SendFinalOutputEmailArgs) -> str:
    """Send plain-text email to the preconfigured recipient (SENDGRID_TO_EMAIL / server default). There is no per-request recipient field—do not ask the user which address to use unless they need a different destination (not supported by this tool). Call only when the user explicitly asked to receive an email."""
    if not SENDGRID_API_KEY:
        return "Email not sent: SENDGRID_API_KEY is not set."
    if not FROM_EMAIL or not TO_EMAIL:
        return "Email not sent: set SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL."

    body = (args.body or "").strip()
    if not body:
        return "Email not sent: body was empty."
    if len(body) > 500_000:
        body = body[:500_000] + "\n\n[truncated for SendGrid size limits]"

    from_email = Email(FROM_EMAIL)
    to_email = To(TO_EMAIL)
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, args.subject, content).get()
    sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = sg.client.mail.send.post(request_body=mail)
    if response.status_code not in (200, 202):
        return f"Email failed: HTTP {response.status_code}"
    return "Email sent successfully."


if __name__ == "__main__":
    mcp.run(transport="stdio")
