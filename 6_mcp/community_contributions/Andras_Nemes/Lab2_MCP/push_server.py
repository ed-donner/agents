import os
from dotenv import load_dotenv
import requests
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

mcp = FastMCP("push_server")

@mcp.tool()
async def push(message: str) -> str:
    """Send a push notification to the user's phone.

    Args:
        message: A brief message to send as the push notification
    """
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    response = requests.post(pushover_url, data=payload, timeout=10)
    response.raise_for_status()
    return "Push notification sent"

if __name__ == "__main__":
    mcp.run(transport="stdio")
