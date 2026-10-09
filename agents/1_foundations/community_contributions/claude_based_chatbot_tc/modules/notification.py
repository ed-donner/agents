"""
Push notification system using Pushover
"""
import requests
from .config import PUSHOVER_USER, PUSHOVER_TOKEN

def push(text):
    """Send push notifications via Pushover"""
    if PUSHOVER_USER and PUSHOVER_TOKEN:
        print(f"Push: {text}")
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "message": text,
            }
        )
    else:
        print(f"Push notification (not sent): {text}")