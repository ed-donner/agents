import os
from typing import Dict
from dotenv import load_dotenv

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool, ModelSettings

load_dotenv(override=True)

# Email addresses are stored in .env file
SENDFROM = os.environ.get('EMAIL_FROM')  # stored as secrets
SENDTO = os.environ.get('EMAIL_TO')  # stored as secrets

EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(SENDFROM)
    to_email = To(SENDTO)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"


email_agent = Agent(
    name="Email agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)