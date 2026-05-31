import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
import mailtrap

load_dotenv(override=True)

mailtrap_api_key = os.getenv("MAILTRAP_API_KEY")
sender_email = os.getenv("EMAIL_SENDER")
receiver_email = os.getenv("EMAIL_RECEIVER")

if not mailtrap_api_key:
    raise ValueError("Mailtrap API key is required")

if not sender_email:
    raise ValueError("Email sender is required")

if not receiver_email:
    raise ValueError("Email receiver is required")

mcp = FastMCP("email_server")


class EmailModelArgs(BaseModel):
    content: str = Field(description="email content")
    subject: str = Field(description="email subject")

@mcp.tool()
def send_email(args: EmailModelArgs):
    """Send an email with the given content and subject"""
    print(f"Sending email: {args.subject} to {receiver_email}")
    try:
      client = mailtrap.MailtrapClient(token=mailtrap_api_key)
      mail = mailtrap.Mail(
          sender=mailtrap.Address(email=sender_email, name="Dear User"),
          to=[mailtrap.Address(email=receiver_email)],
          subject=args.subject,
          html=args.content,
      )
      client.send(mail)
      return "Email sent successfully"
    except Exception as e:
      return f"Failed to send email: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")