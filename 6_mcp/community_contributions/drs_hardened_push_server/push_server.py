import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_API = "https://api.pushover.net/1"
pushover_url = PUSHOVER_API + "/messages.json"
pushover_validate_url = PUSHOVER_API + "/users/validate.json"


mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")

   
@mcp.tool()
def push(args: PushModelArgs):
    """Send a push notification with this brief message
    Returns a message starting with 'FAILED' if the notification could not be delivered."""
    if not pushover_token or not pushover_user:
        return "FAILED: PUSHOVER_TOKEN and/or PUSHOVER_USER are not set"
    try:
        # messages.json reports success even when the user has no active devices (e.g. an
        # expired trial) and the message is silently dropped, so validate the user first
        validate_payload = {"user": pushover_user, "token": pushover_token}
        validate = requests.post(pushover_validate_url, data=validate_payload, timeout=10)
        info = validate.json()
        if info.get("status") != 1:
            return f"FAILED: Pushover validation failed: {info.get('errors')}"


        print(f"Push: {args.message}")
        payload = {"user": pushover_user, "token": pushover_token, "message": args.message}
        response = requests.post(pushover_url, data=payload, timeout=10)
        result = response.json()
        if response.status_code != 200 or result.get("status") != 1:
            return f"FAILED: Pushover returned HTTP {response.status_code}: {result.get('errors')}"
    except (requests.RequestException, ValueError) as e:
        return f"FAILED: could not reach Pushover: {e}"

    return "Push notification sent"


if __name__ == "__main__":
    mcp.run(transport="stdio")
