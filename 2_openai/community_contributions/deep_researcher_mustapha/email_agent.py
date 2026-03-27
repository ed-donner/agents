"""
email_agent.py — Sends the final report as a formatted HTML email.
Uses Gmail SMTP (SSL port 465). Credentials must be set in .env:
  EMAIL=you@gmail.com
  PASSWORD=your_app_password
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from agents import Agent, function_tool
from deep_research import MODEL_CAPABLE


# ── Tool ─────────────────────────────────────────────────────────────────────

@function_tool
def send_email(subject: str, html_body: str, recipient: str = None) -> str:
    """Send an HTML email. Returns 'success' or an error message."""
    try:
        email_user = os.environ.get("EMAIL")
        email_password = os.environ.get("PASSWORD")
        target = recipient or email_user

        if not email_user or not email_password:
            return "Error: EMAIL or PASSWORD not set in environment."
        if not target:
            return "Error: No recipient email address provided."

        msg = MIMEMultipart()
        msg["From"] = f"Deep Researcher <{email_user}>"
        msg["To"] = target
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(email_user, email_password)
            server.send_message(msg)

        return f"success: email sent to {target}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


# ── Agent definition ─────────────────────────────────────────────────────────

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a FINAL REPORT and RESEARCH PROCESS DETAILS. 
Use your tool to send one email: convert both sections into clean, professional HTML.
- The Final Report should be the main body.
- The Research Process Details should be a clearly labeled 'Behind the Scenes' section below the report.
- Include a relevant subject line and always send to the recipient email provided."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=MODEL_CAPABLE,
)
