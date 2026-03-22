import os
from typing import Dict, Literal

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool
from email.mime.text import MIMEText
import smtplib

from openai_compat import AGENT_MODEL


def _email_provider() -> Literal["gmail", "sendgrid"]:
    """Prefer Gmail SMTP when configured; otherwise SendGrid. Set EMAIL_PROVIDER to force one."""
    forced = (os.getenv("EMAIL_PROVIDER") or "").strip().lower()
    if forced == "gmail":
        if not (os.getenv("GMAIL_APP_PASSWORD") and os.getenv("GMAIL_ADDRESS")):
            raise ValueError("EMAIL_PROVIDER=gmail requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")
        return "gmail"
    if forced == "sendgrid":
        if not os.getenv("SENDGRID_API_KEY"):
            raise ValueError("EMAIL_PROVIDER=sendgrid requires SENDGRID_API_KEY in .env")
        if not os.getenv("SENDGRID_FROM_EMAIL") or not os.getenv("SENDGRID_TO_EMAIL"):
            raise ValueError("EMAIL_PROVIDER=sendgrid requires SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL in .env")
        return "sendgrid"
    if os.getenv("GMAIL_APP_PASSWORD") and os.getenv("GMAIL_ADDRESS"):
        return "gmail"
    if os.getenv("SENDGRID_API_KEY"):
        if not os.getenv("SENDGRID_FROM_EMAIL") or not os.getenv("SENDGRID_TO_EMAIL"):
            raise ValueError(
                "SendGrid needs SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL — or add GMAIL_ADDRESS + GMAIL_APP_PASSWORD to use Gmail SMTP instead."
            )
        return "sendgrid"
    raise ValueError(
        "Set up email in .env: GMAIL_ADDRESS + GMAIL_APP_PASSWORD (Gmail), "
        "or SENDGRID_API_KEY + SENDGRID_FROM_EMAIL + SENDGRID_TO_EMAIL (SendGrid)."
    )


def send_lab_email(subject: str, body: str, *, subtype: Literal["plain", "html"] = "plain") -> None:
    """Send one message via Gmail or SendGrid (see _email_provider)."""
    prov = _email_provider()
    if prov == "gmail":
        user = os.environ["GMAIL_ADDRESS"].strip()
        pwd = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
        to_addr = (os.getenv("GMAIL_TO_EMAIL") or user).strip()
        msg = MIMEText(body, subtype, "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_addr
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(user, pwd)
            smtp.sendmail(user, [to_addr], msg.as_string())
        return
    from_addr = os.environ.get("SENDGRID_FROM_EMAIL")
    to_addr = os.environ.get("SENDGRID_TO_EMAIL")
    if not from_addr or not to_addr:
        raise ValueError("SendGrid needs SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL in .env")
    content_type = "text/html" if subtype == "html" else "text/plain"
    sg = sendgrid.SendGridAPIClient(api_key=os.environ["SENDGRID_API_KEY"])
    mail = Mail(Email(from_addr), To(to_addr), subject, Content(content_type, body)).get()
    response = sg.client.mail.send.post(request_body=mail)
    if response.status_code >= 400:
        raise RuntimeError(f"SendGrid HTTP {response.status_code}: {response.body}")



@function_tool
def send_email(subject: str, html_body: str)->Dict[str,str]:
    """Send an email with the given subject and HTML body to the configured recipient."""
    send_lab_email(subject, html_body, subtype="html")
    return "success"
# @function_tool
# def send_email(subject: str, html_body: str) -> Dict[str, str]:
#     """Send an email with the given subject and HTML body"""
#     sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
#     from_email = Email("ed@edwarddonner.com")  # put your verified sender here
#     to_email = To("ed.donner@gmail.com")  # put your recipient here
#     content = Content("text/html", html_body)
#     mail = Mail(from_email, to_email, subject, content).get()
#     response = sg.client.mail.send.post(request_body=mail)
#     print("Email response", response.status_code)
#     return "success"


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=AGENT_MODEL,
)
