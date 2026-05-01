from sendgrid.helpers.mail import Mail, From, To
from typing import Dict
import os
from agents import Agent, function_tool
import sendgrid 

from models.models import ReportData 

@function_tool
def send_email(subject:str, html_body:str) -> Dict[str, str]:
    """Send out an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    mail = Mail(
        from_email=From("mohan.goyal@mogomantra.com"),
        to_emails=To("mohanrajgoyal@gmail.com"),
        subject=subject,
        html_content=html_body,
    ).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"


EMAIL_INSTRUCTIONS = """You send a single polished HTML email based on a research report.
You will be given:
- a short summary
- a detailed markdown report
- follow-up questions

Create a clear subject line, convert the markdown report into clean HTML, include the summary near the top,
and include the follow-up questions in their own section at the end. Then use the tool once to send the email."""

email_agent = Agent(
    name = "Email Agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools = [send_email],
    model = "gpt-4o-mini",
)
