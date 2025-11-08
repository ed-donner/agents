from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import requests


class PushoverNotificationInput(BaseModel):
    """Input schema for PushoverNotificationTool."""
    message: str = Field(..., description="The message to send via Pushover notification.")


class PushoverNotificationTool(BaseTool):
    name: str = "Pushover Notification Tool"
    description: str = (
        "Use this tool to send a notification message via Pushover API when a task is completed. "
        "This tool should be called after completing your main work to notify that the task is done. "
        "Provide a clear message describing what was completed. "
        "Requires PUSHOVER_USER and PUSHOVER_TOKEN environment variables to be set."
    )
    args_schema: Type[BaseModel] = PushoverNotificationInput

    def _run(self, message: str) -> str:
        """Send a Pushover notification with the given message."""
        pushover_token="aoi5ezd1rt32bbvffqc8um8gif2fkx"   
        pushover_user="usutk7kv1812bxkzun3tnt8ipimt31"
        pushover_url = "https://api.pushover.net/1/messages.json"

        if not pushover_user:
            error_msg = "Pushover user not found. Please set PUSHOVER_USER environment variable."
            print(error_msg)
            return error_msg

        if not pushover_token:
            error_msg = "Pushover token not found. Please set PUSHOVER_TOKEN environment variable."
            print(error_msg)
            return error_msg

        print(f"Pushover user found and starts with {pushover_user[0]}")
        print(f"Pushover token found and starts with {pushover_token[0]}")
        print(f"Pushing message: {message}")

        payload = {
            "user": pushover_user,
            "token": pushover_token,
            "message": message
        }

        try:
            response = requests.post(pushover_url, data=payload)
            response.raise_for_status()
            result = f"Notification sent successfully: {response.json()}"
            print(result)
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send Pushover notification: {str(e)}"
            print(error_msg)
            return error_msg

