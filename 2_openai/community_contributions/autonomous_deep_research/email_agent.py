import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool
from pydantic import BaseModel, Field


class Email(BaseModel):
    html_subject: str = Field(description="Subject of an email formateed in HTML")
    html_body: str = Field(description="Body of the email formatted in HTML")

    def __str__(self) -> str:
        return self.html_body


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

@function_tool
def send_email(email: Email) -> Email: 
    """ Send an email with the given subject and HTML body """
    print ("Email Subject: ", email.html_subject)
    return email


email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    handoff_description="Sends an email",
    output_type=Email,
)

email_agent_tool = email_agent.as_tool(tool_name="email_sender", tool_description="Sends an email")
