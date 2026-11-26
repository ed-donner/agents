"""Week 6 Day 2 exercise: my own MCP server with one tool that sends a push notification.

The notebook starts this file as a subprocess and talks to it over stdin/stdout:
    uv run my_push_server.py
"""

import os

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Read PUSHOVER_USER and PUSHOVER_TOKEN from the repo-root .env file.
load_dotenv(override=True)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# The server's name, shown to any client that connects.
mcp = FastMCP("my_push_server")


# The pydantic model defines the tool's argument schema; the Field description is what
# the model reads to know what to put in `message`.
class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")


# @mcp.tool() turns a typed function into an MCP tool: the argument type becomes the
# schema and the docstring becomes the description the model reads.
@mcp.tool()
def push(args: PushModelArgs) -> str:
    """Send a push notification to the user's phone with this brief message."""
    payload = {
        "user": PUSHOVER_USER,
        "token": PUSHOVER_TOKEN,
        "message": args.message,
    }
    requests.post(PUSHOVER_URL, data=payload)
    return "Push notification sent"


if __name__ == "__main__":
    # stdio: the client launches this script and exchanges messages over stdin/stdout.
    mcp.run(transport="stdio")
