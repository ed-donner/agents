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
    # ntfy.sh is free with no account: subscribe to NTFY_TOPIC in the ntfy phone app to receive these
    ntfy_topic = os.getenv("NTFY_TOPIC")
    if not ntfy_topic:
        return "Push notification not sent: NTFY_TOPIC is not set in .env"
    ntfy_url = f"https://ntfy.sh/{ntfy_topic}"
    result = requests.post(ntfy_url, data=message.encode("utf-8"),
                           headers={"Title": "Stock Picker"}, timeout=10).status_code
    return f"Push notification sent with API response code: {result}"
