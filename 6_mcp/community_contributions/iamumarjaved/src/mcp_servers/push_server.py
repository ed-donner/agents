import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp.server.fastmcp import FastMCP
from src.database.database import write_log
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

mcp = FastMCP("push_notification_server")

@mcp.tool(description="Send push notification to mobile device via Pushover")
async def send_push_notification(name: str, message: str) -> str:
    """
    Send push notification to mobile device via Pushover.

    Args:
        name: Trader's name for notification title and logging
        message: Notification message content (trading summary, portfolio status, etc.)

    Returns:
        Confirmation message indicating notification was sent or logged
    """
    write_log(name, "notification", message)

    if pushover_user and pushover_token:
        try:
            payload = {
                "user": pushover_user,
                "token": pushover_token,
                "message": f"{name}: {message}",
                "title": f"Trading Floor - {name}"
            }
            response = requests.post(pushover_url, data=payload, timeout=5)
            if response.status_code == 200:
                return f"Push notification sent to Pushover for {name}"
            else:
                return f"Notification logged (Pushover error: {response.status_code})"
        except Exception as e:
            return f"Notification logged (Pushover failed: {str(e)})"

    return f"Notification logged for {name} (Pushover not configured)"

if __name__ == "__main__":
    mcp.run(transport='stdio')
