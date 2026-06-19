import requests
from typing import Dict
from agents import Agent, function_tool
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# === CONFIGURATION CONSTANTS ===
PUBLIC_KEY: str =  os.getenv('EJS_PUBLIC_KEY')
SERVICE_ID: str = os.getenv('EJS_SERVICE_ID')
TEMPLATE_ID: str = os.getenv('EJS_TEMPLATE_ID')
ACCESS_TOKEN: str = os.getenv('EJS_ACCESS_TOKEN')
EMAIL_API_URL: str = "https://api.emailjs.com/api/v1.0/email/send"
SELF_COPY_EMAIL: str = os.getenv('EJS_SELF_EMAIL')

def build_email_payload(email: str, subject: str, html_body: str) -> Dict:
    return {
        "service_id": SERVICE_ID,
        "template_id": TEMPLATE_ID,
        "user_id": PUBLIC_KEY,
        "accessToken": ACCESS_TOKEN,
        "template_params": {
            "email": email,
            "subject": subject,
            "content": html_body
        }
    }


@function_tool
def send_email(subject: str, html_body: str, email: str) -> Dict[str, str]:
    if email != "None":
        user_payload = build_email_payload(email, subject, html_body)
        response = requests.post(url=EMAIL_API_URL, json=user_payload)
        print(response.text)

    # Always send a self-copy
    dev_payload = build_email_payload(SELF_COPY_EMAIL, subject, html_body)
    response = requests.post(url=EMAIL_API_URL, json=dev_payload)
    print(response.text)
    return {"status": "ok"}


INSTRUCTIONS = """
You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email,
providing the report converted into clean, well presented HTML with an appropriate subject line.
"""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
