import requests
from typing import Dict
from agents import Agent, function_tool
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# === CONFIGURATION CONSTANTS ===
PUBLIC_KEY: str = os.getenv('EJS_PUBLIC_KEY')  # Your EmailJS Public Key (user_id)
SERVICE_ID: str = os.getenv('EJS_SERVICE_ID')  # Your EmailJS Service ID
TEMPLATE_ID: str = os.getenv('EJS_TEMPLATE_ID')  # Your EmailJS Template ID
EMAIL_API_URL: str = "https://api.emailjs.com/api/v1.0/email/send"
SELF_COPY_EMAIL: str = os.getenv('EJS_SELF_EMAIL')  # Optional: for self-copies


def build_email_payload(email: str, subject: str, html_body: str) -> Dict:
    return {
        "service_id": SERVICE_ID,
        "template_id": TEMPLATE_ID,
        "user_id": PUBLIC_KEY,
        "template_params": {
            "email": email,
            "subject": subject,
            "content": html_body
        }
    }


@function_tool
def send_email(subject: str, html_body: str, email: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body using EmailJS"""
    if email != "None" and email:
        user_payload = build_email_payload(email, subject, html_body)
        try:
            response = requests.post(url=EMAIL_API_URL, json=user_payload)
            print(f"EmailJS response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending email: {e}")

    # Always send a self-copy if configured
    if SELF_COPY_EMAIL:
        dev_payload = build_email_payload(SELF_COPY_EMAIL, subject, html_body)
        try:
            response = requests.post(url=EMAIL_API_URL, json=dev_payload)
            print(f"EmailJS self-copy response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending self-copy: {e}")
    
    return {"status": "ok"}


INSTRUCTIONS = """
You are able to send a nicely formatted HTML email based on a detailed medical research report.
You will be provided with a detailed medical literature review report. You should use your tool to send one email,
providing the report converted into clean, well presented HTML with an appropriate subject line that reflects the medical topic.
The email parameter should be the recipient's email address.
"""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)

