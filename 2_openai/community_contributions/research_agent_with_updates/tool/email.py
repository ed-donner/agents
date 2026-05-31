import os
from typing import Dict

import sendgrid
from agents import (
    Agent,
    function_tool,
)
from sendgrid.helpers.mail import (
    Content,
    Email,
    Mail,
    To,
)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("antcarrealty@gmail.com")
    to_email = To("antonio.pisani@gmail.com")
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return {"status": "success"}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-5.2",
)

send_email_tool = email_agent.as_tool(
    tool_name="send_email_tool",
    tool_description="Sends a nicely formatted HTML email based on a detailed report.",
)
