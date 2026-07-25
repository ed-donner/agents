import os
from typing import Dict

import resend
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body."""
    resend.api_key = os.environ["RESEND_API_KEY"]
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": os.environ["RESEND_TO_EMAIL"],
        "subject": subject,
        "html": html_body,
    })
    return {"status": "success"}


INSTRUCTIONS = (
    "You send the final learning roadmap email. "
    "The email must include the full generated roadmap content in polished HTML, "
    "not just a short confirmation or preview. "
    "It must also include the file path of the exported document. "
    "Send exactly one email using your tool."
)

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
