import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

if pushover_user is None or pushover_token is None:
    raise ValueError("Pushover credentials are required!")

if pushover_url is None:
    raise ValueError("Pushover URL is required!")


mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")


@mcp.tool()
def push(args: PushModelArgs):
    """Send a push notification with this brief message"""
    try:
      print(f"Push: {args.message}")
      payload = {"user": pushover_user, "token": pushover_token, "message": args.message}
      result = requests.post(pushover_url, data=payload)
      result.raise_for_status()
      return "Push notification sent"
    except Exception as e:
      return f"Failed to send push notification: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
