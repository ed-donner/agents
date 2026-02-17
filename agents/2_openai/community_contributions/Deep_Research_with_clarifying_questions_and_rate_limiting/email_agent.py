import os
import base64
import requests
from agents import Agent, function_tool

@function_tool
def send_email(subject: str, html_body: str, to: str):
    """Send out an email with the given subject and HTML body to a specified recipient using Mailgun"""
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN')

    if not all([MAILGUN_API_KEY, MAILGUN_DOMAIN, to]):
        return {"status": "failure", "response": "Missing configuration or recipient"}

    auth = base64.b64encode(f'api:{MAILGUN_API_KEY}'.encode()).decode()
    response = requests.post(
        f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages',
        headers={
            'Authorization': f'Basic {auth}'
        },
        data={
            'from': f'Research Agent <mailgun@{MAILGUN_DOMAIN}>',
            'to': to,
            'subject': subject,
            'html': html_body
        }
    )

    return {
        "status": "success" if response.status_code == 200 else "failure",
        "response": response.text
    }

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report and a recipient email. Use your tool to send one email, 
providing the report as HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
