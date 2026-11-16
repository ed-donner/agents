import os

import requests
from dotenv import load_dotenv


load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str) -> None:
    """Send a text message to the configured Telegram chat."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID is not set in .env")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
        timeout=10,
    )
    response.raise_for_status()


def send_email(subject: str, text_body: str, html_body: str = "") -> None:
    """Compatibility wrapper: send the former email content to Telegram."""
    del html_body
    send_telegram_message(f"{subject}\n\n{text_body}")


def push(message: str) -> None:
    """Compatibility wrapper for code that previously used Pushover."""
    send_telegram_message(message)

