"""
Email Agent - sends the final report as a nicely formatted HTML email.

Adapted from the original deep_research implementation.
Uses the Mailjet API for email delivery.
"""

import os
from typing import Dict

from mailjet_rest import Client
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body."""
    api_key = os.environ.get("MAILJET_API_KEY")
    secret_key = os.environ.get("MAILJET_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("Warning: MAILJET_API_KEY or MAILJET_SECRET_KEY not found. Email not sent.")
        return {"status": "skipped", "reason": "No API keys configured"}
    
    # Read from environment variables
    from_addr = os.environ.get("FROM_EMAIL")
    from_name = os.environ.get("FROM_NAME", "Deep Research")
    to_addr = os.environ.get("TO_EMAIL")
    to_name = os.environ.get("TO_NAME", "")
    
    if not from_addr or not to_addr:
        print("Warning: FROM_EMAIL or TO_EMAIL not configured. Email not sent.")
        return {"status": "skipped", "reason": "Email addresses not configured"}
    
    try:
        mailjet = Client(auth=(api_key, secret_key), version="v3.1")
        
        data = {
            "Messages": [
                {
                    "From": {"Email": from_addr, "Name": from_name},
                    "To": [{"Email": to_addr, "Name": to_name}],
                    "Subject": subject,
                    "HTMLPart": html_body,
                }
            ]
        }
        
        response = mailjet.send.create(data=data)
        
        print(f"Email response: {response.status_code}")
        return {"status": "success", "code": str(response.status_code)}
    
    except Exception as e:
        print(f"Email send failed: {e}")
        return {"status": "error", "message": str(e)}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a research report.

You will be provided with a markdown report. Your job is to:
1. Convert it to clean, well-presented HTML
2. Create an appropriate subject line
3. Send it using your email tool

## HTML Formatting Guidelines

- Use a clean, professional style
- Include proper headings (h1, h2, h3)
- Use bullet points and numbered lists where appropriate
- Keep paragraphs readable (not too long)
- Include a brief intro before the main content
- Add a footer noting this was auto-generated

Make the email something a busy executive would appreciate receiving.
"""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
