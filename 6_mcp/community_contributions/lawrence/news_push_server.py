import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv()

PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

if not PUSHOVER_USER or not PUSHOVER_TOKEN:
    raise ValueError("Pushover credentials required")

mcp = FastMCP("push_server")

class PushArgs(BaseModel):
    message: str = Field(description="Message to push")

@mcp.tool()
def push(args: PushArgs):
    try:
        url = "https://api.pushover.net/1/messages.json"
        payload = {
            "user": PUSHOVER_USER,
            "token": PUSHOVER_TOKEN,
            "message": args.message,
        }
        r = requests.post(url, data=payload)
        r.raise_for_status()
        return "Push sent!"
    except Exception as e:
        return f"Push failed: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
