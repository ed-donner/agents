import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool

from config import EMAIL_MODEL_SETTINGS


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_addr = os.environ.get("SENDGRID_FROM")
    to_addr = os.environ.get("SENDGRID_TO")
    if not api_key:
        return {"status": "error", "message": "SENDGRID_API_KEY is not set"}
    if not from_addr:
        return {"status": "error", "message": "SENDGRID_FROM is not set"}
    if not to_addr:
        return {"status": "error", "message": "SENDGRID_TO is not set"}
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email(from_addr)
    to_email = To(to_addr)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    sg.client.mail.send.post(request_body=mail)
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
    model="gpt-5.4-mini",
    model_settings=EMAIL_MODEL_SETTINGS,
)
