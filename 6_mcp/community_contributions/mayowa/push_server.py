import os

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

mcp = FastMCP("research_push_server")


@mcp.tool()
def push(message: str, title: str = "Deep Research Complete") -> str:
    """Send a concise push notification announcing that research has completed."""
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")

    if not pushover_user or not pushover_token:
        return (
            "Push notification skipped: PUSHOVER_USER or PUSHOVER_TOKEN is not configured "
            "for the push server process."
        )

    payload = {
        "user": pushover_user,
        "token": pushover_token,
        "title": title,
        "message": message,
    }
    response = requests.post(PUSHOVER_URL, data=payload, timeout=15)
    if response.ok:
        return "Push notification sent."
    return f"Push notification failed: {response.status_code} {response.text}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
