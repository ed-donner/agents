from dotenv import load_dotenv
import requests
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_FILE, override=True)


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def send_email(subject, text_body, html_body):
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)


pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)


def send_telegram(message):
    """Send one plain-text message to the chat configured in the root .env."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise RuntimeError(
            f"Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in {ENV_FILE}"
        )
    if not message.strip():
        raise ValueError("Telegram message cannot be empty")
    if len(message) > 4000:
        raise ValueError("Telegram message is too long; keep it under 4000 characters")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=30,
    )
    try:
        result = response.json()
    except ValueError:
        result = {}
    if not response.ok or not result.get("ok"):
        raise RuntimeError(
            f"Telegram API error ({response.status_code}): "
            f"{result.get('description', response.text or 'unknown error')}"
        )
