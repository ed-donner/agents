import os
from typing import Dict

#import sendgrid
#from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool
import resend

@function_tool
def send_email(subject: str, html_body: str) -> str:
    """ Send out an email with the given subject and HTML body """
    resend.Emails.send({
        "from": "onboarding@resend.dev",  # works without domain auth
        "to": "vanbecelaere.kevin@gmail.com",
        "subject": subject,
        "html": html_body,
    })
    return "success"


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
