from typing import Dict
import os

from agents import Agent, function_tool
from brevo import Brevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body """
    client = Brevo(api_key=os.environ.get('BREVO_API_KEY'))
    result = client.transactional_emails.send_transac_email(
        subject=subject,
        html_content=html_body,
        sender=SendTransacEmailRequestSender(
            email="[EMAIL_ADDRESS]",
        ),
        to=[
            SendTransacEmailRequestToItem(
                email="[EMAIL_ADDRESS]",
                name="John Doe",
            )
        ],
    )
    print("Email sent. Message ID:", result.message_id)

    return "success"

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a catchy newsletter.
You will be provided with a catchy newsletter content. You should use your tool to send one email, providing the 
newsletter converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
