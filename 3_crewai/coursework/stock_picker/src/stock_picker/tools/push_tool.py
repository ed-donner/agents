from crewai.tools import tool
import os
import requests


@tool("Send Push Notification")
def send_push_notification(message: str) -> str:
    """
    Use this tool to send a push notification to the user.
    Args:
        message: The message to be sent as a push notification to the user.
    Returns:
        A string indicating the status of the push notification.
    """
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_url = "https://api.pushover.net/1/messages.json"
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    result = requests.post(pushover_url, data=payload).status_code
    return f"Push notification sent with API response code: {result}"