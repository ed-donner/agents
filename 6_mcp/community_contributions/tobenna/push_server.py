import os

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

load_dotenv(override=True)

PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

mcp = FastMCP("lead_push_server")


class PushArgs(BaseModel):
    message: str = Field(description="A concise sales alert to send via push notification")


@mcp.tool()
def push(args: PushArgs) -> str:
    """Send a push notification with a concise sales alert."""
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        return "Push notification skipped: PUSHOVER_USER or PUSHOVER_TOKEN is not configured"

    payload = {
        "user": PUSHOVER_USER,
        "token": PUSHOVER_TOKEN,
        "message": args.message,
    }
    response = requests.post(PUSHOVER_URL, data=payload, timeout=15)
    if response.ok:
        return "Push notification sent"
    return f"Push notification failed: {response.status_code} {response.text}"


if __name__ == "__main__":
    mcp.run(transport="stdio")