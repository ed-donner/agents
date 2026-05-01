import os

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

mcp = FastMCP("push_server")

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


@mcp.tool()
def push(message: str, title: str = "What's happening?") -> str:
    """Send a push notification via Pushover.

    Args:
        message: The notification body to send.
        title: Notification title (default: "What's happening?").
    """
    user = os.getenv("PUSHOVER_USER")
    token = os.getenv("PUSHOVER_TOKEN")
    if not user or not token:
        return "Push skipped: PUSHOVER_USER or PUSHOVER_TOKEN not set."

    payload = {"user": user, "token": token, "message": message, "title": title}
    try:
        r = requests.post(PUSHOVER_URL, data=payload, timeout=15)
        r.raise_for_status()
        return "Push notification sent."
    except Exception as e:
        return f"Failed to send push notification: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
