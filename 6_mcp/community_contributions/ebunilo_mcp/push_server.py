import os

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")


@mcp.tool()
def push(args: PushModelArgs):
    """Send a push notification with this brief message (optional credentials)."""
    print(f"Push: {args.message}")
    if not pushover_user or not pushover_token:
        return "Push skipped: PUSHOVER_USER / PUSHOVER_TOKEN not set"
    payload = {"user": pushover_user, "token": pushover_token, "message": args.message}
    requests.post(pushover_url, data=payload, timeout=15)
    return "Push notification sent"


if __name__ == "__main__":
    mcp.run(transport="stdio")
