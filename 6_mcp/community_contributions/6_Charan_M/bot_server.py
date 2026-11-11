import os
from typing import Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_notification(
    message: str, 
    title: Optional[str] = None, 
    url: Optional[str] = None
) -> str:
    """
    Send a message directly to a Telegram chat using a Telegram Bot.
    
    Args:
        message: The main text of the notification.
        title: An optional title for the notification.
        url: An optional URL to include with the message.
    """
    print(f"Sending Telegram notification: {message}")
    
    if not telegram_token or not telegram_chat_id:
        return "Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing in .env file."
        
    telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    
    # Format the text to include the title and url if present
    text = message
    if title:
        text = f"<b>{title}</b>\n\n{text}"
    if url:
        text = f"{text}\n\n{url}"
        
    payload = {
        "chat_id": telegram_chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    response = requests.post(telegram_url, json=payload)
    if response.status_code == 200:
        return f"Telegram notification successfully sent! Message: {message}"
    else:
        return f"Failed to send Telegram notification. Status code: {response.status_code}, Response: {response.text}"
