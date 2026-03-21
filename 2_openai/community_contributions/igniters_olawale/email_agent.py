import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

from agents import Agent, function_tool

from config import model


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    host = os.environ.get("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io")
    port = int(os.environ.get("MAILTRAP_SMTP_PORT", "2525"))
    user = os.environ.get("MAILTRAP_SMTP_USER")
    password = os.environ.get("MAILTRAP_SMTP_PASSWORD")
    if not user or not password:
        return {"status": "skipped", "message": "MAILTRAP_SMTP_USER or MAILTRAP_SMTP_PASSWORD not set"}

    from_addr = os.environ.get("MAILTRAP_FROM", "sender@example.com")
    to_addr = os.environ.get("MAILTRAP_TO", "adeogun161@gmail.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(host, port) as s:
            s.login(user, password)
            s.sendmail(from_addr, to_addr, msg.as_string())
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e).strip() or "Send failed"}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=model,
    handoff_description="Send the research report by email. Pass the report content.",
)
