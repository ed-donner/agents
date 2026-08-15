from dotenv import load_dotenv, find_dotenv
import requests
import os

load_dotenv(find_dotenv(usecwd=True), override=True)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

def send_email(subject, text_body, html_body, to_email=None):
    recipient = to_email.strip() if to_email and to_email.strip() else EMAIL_ADDRESS
    if not recipient:
        raise ValueError("No recipient email address provided.")
    if not RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY environment variable is missing.")

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [recipient],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }
    if EMAIL_ADDRESS:
        payload["reply_to"] = EMAIL_ADDRESS

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

