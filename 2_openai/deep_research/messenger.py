from dotenv import load_dotenv, find_dotenv
import requests
import os

load_dotenv(find_dotenv(usecwd=True), override=True)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "bhupeshdanewaa@gmail.com")

def send_email(subject, text_body, html_body, to_email=None):
    recipient = to_email.strip() if to_email and to_email.strip() else EMAIL_ADDRESS
    if not recipient:
        raise ValueError("No recipient email address provided.")

    if not SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY environment variable is missing.")

    sender_name = os.getenv("EMAIL_SENDER_NAME", "Deep Research AI")

    # Add transactional email footer to reduce spam score
    footer_text = "\n\n---\nThis research report was requested and sent via Deep Research AI."
    footer_html = '<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0 10px 0;"><p style="font-size: 12px; color: #64748b; text-align: center;">This research report was requested and sent via Deep Research AI.</p>'

    full_text = f"{text_body}{footer_text}"
    full_html = f"{html_body}{footer_html}" if "</html>" not in html_body else html_body.replace("</html>", f"{footer_html}</html>")

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": EMAIL_ADDRESS, "name": sender_name},
        "reply_to": {"email": EMAIL_ADDRESS, "name": sender_name},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": full_text},
            {"type": "text/html", "value": full_html},
        ],
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.status_code


pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

