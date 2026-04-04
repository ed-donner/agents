import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

pushover_user  = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url   = "https://api.pushover.net/1/messages.json"

mcp = FastMCP("push_server")


@mcp.tool()
def push(message: str) -> str:
    """Send a push notification with this brief message.

    Args:
        message: A brief message to push to the user's phone.
    """
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)
    return "Push notification sent"


if __name__ == "__main__":
    mcp.run(transport="stdio")