import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To, Cc
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("temmyogunbo@gmail.com")  # put your verified sender here
    to_email = To("ogunbotemilola@yahoo.com")  # put your recipient here
    cc_email = Cc("ruthogunbo@gmail.com") # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content)
    mail.add_cc(cc_email)
    response = sg.client.mail.send.post(request_body=mail.get())
    print("Email response", response.status_code)
    return "success"


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report on food and drugs.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
