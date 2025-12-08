import os
from typing import Dict

import resend
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str, email_to: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    resend.api_key = os.environ.get('RESEND_API_KEY')
    params = {
        "from": "service@yourdomain.com",
        "to": [f"{email_to}"],
        "subject": subject,
        "html": html_body,
        "reply_to": "service@yourdomain.com"
    }
    
    response = resend.Emails.send(params)
    return {"status": "success", "id": response.get("id")}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report and email address. You should use your tool to send one email using the email address, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
