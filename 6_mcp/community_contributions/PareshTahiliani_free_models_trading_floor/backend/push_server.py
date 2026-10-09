import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

ntfy_topic = os.getenv("NTFY_TOPIC")
ntfy_url = f"https://ntfy.sh/{ntfy_topic}"


mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")


@mcp.tool()
def push(args: PushModelArgs):
    """Send a push notification with this brief message"""
    print(f"Push: {args.message}")
    if not ntfy_topic:
        return "Push notification not sent: NTFY_TOPIC is not set in .env"
    # ntfy.sh is free with no account: subscribe to NTFY_TOPIC in the ntfy phone app to receive these
    requests.post(ntfy_url, data=args.message.encode("utf-8"), headers={"Title": "Trading Floor"}, timeout=10)
    return "Push notification sent"


if __name__ == "__main__":
    mcp.run(transport="stdio")
