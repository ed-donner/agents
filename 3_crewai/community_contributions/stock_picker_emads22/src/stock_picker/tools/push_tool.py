from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import requests
import json


class PushNotification(BaseModel):
    """A message to be sent to the user"""

    message: str = Field(..., description="The message to be sent to the user.")


class PushNotificationTool(BaseTool):
    # Tool name shown to the LLM
    name: str = "Send a Push Notification"

    # Short description of what the tool does
    description: str = "This tool is used to send a push notification to the user."

    # Expected input schema for validation
    args_schema: Type[BaseModel] = PushNotification

    def _run(self, message: str) -> str:
        """
        Core logic executed when the tool is called.
        'message' corresponds to the attribute defined in the PushNotification
        Pydantic model specified as args_schema above.
        Reads credentials, sends the message to Pushover, and returns a confirmation.
        """

        # Load credentials from environment variables
        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_token = os.getenv("PUSHOVER_TOKEN")

        # Pushover API endpoint
        pushover_url = "https://api.pushover.net/1/messages.json"

        # Print message for debugging
        print(f"\nPush: {message}\n")

        # Prepare request payload
        payload = {"user": pushover_user, "token": pushover_token, "message": message}

        # Send POST request
        requests.post(pushover_url, data=payload)

        # Return confirmation
        return json.dumps({"notification": "ok"})
