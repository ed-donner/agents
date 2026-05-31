import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
import logging

load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

# Check if credentials are set
if not pushover_user or not pushover_token:
    logger.warning("PUSHOVER_USER or PUSHOVER_TOKEN not set in environment variables")

mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")


@mcp.tool()
async def push(args: PushModelArgs):
    """Send a push notification with this brief message.
    
    This tool sends a push notification via Pushover. Make sure PUSHOVER_USER 
    and PUSHOVER_TOKEN are set in your .env file.
    """
    if not pushover_user or not pushover_token:
        error_msg = "Pushover credentials not configured. Please set PUSHOVER_USER and PUSHOVER_TOKEN in your .env file."
        logger.error(error_msg)
        return error_msg
    
    try:
        logger.info(f"Sending push notification: {args.message[:50]}...")
        payload = {
            "user": pushover_user,
            "token": pushover_token,
            "message": args.message
        }
        response = requests.post(pushover_url, data=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("status") == 1:
            logger.info("Push notification sent successfully")
            return f"Push notification sent successfully: {args.message}"
        else:
            error_msg = f"Pushover API error: {result.get('errors', 'Unknown error')}"
            logger.error(error_msg)
            return error_msg
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to send push notification: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error sending push notification: {str(e)}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    mcp.run(transport="stdio")
