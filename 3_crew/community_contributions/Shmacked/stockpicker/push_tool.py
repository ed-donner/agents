from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from typing import Type, Any
import os
import requests


def find_key_recursively(obj: Any, key_to_find: str):
    """
    Recursively search nested dicts/lists for a key and return its value.
    Returns None if not found.
    """
    if isinstance(obj, dict):
        if key_to_find in obj:
            return obj[key_to_find]
        for value in obj.values():
            found = find_key_recursively(value, key_to_find)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_key_recursively(item, key_to_find)
            if found is not None:
                return found
    return None


class PushNotificationInput(BaseModel):
    """A message to be sent to the user"""
    message: str = Field(
        ...,
        description="The final string content of the notification to be sent to the user."
    )

    @field_validator("message", mode="before")
    def coerce_message(cls, v):
        # CrewAI sometimes sends nested dicts with metadata
        if isinstance(v, dict):
            # Try to find a nested 'message' or 'description' key
            msg = find_key_recursively(v, "message") or find_key_recursively(v, "description")
            if msg:
                return str(msg)
            # If still not found, just convert dict to string (safe fallback)
            return str(v)
        return str(v)


class PushNotificationTool(BaseTool):
    name: str = "Send a Push Notification"
    description: str = (
        "This tool sends the FINAL PUSH NOTIFICATION to the user. "
        "Use it only when the notification message is fully finalized."
    )
    args_schema: Type[BaseModel] = PushNotificationInput

    def _run(self, message: str) -> str:
        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_token = os.getenv("PUSHOVER_TOKEN")
        pushover_url = "https://api.pushover.net/1/messages.json"

        print(f"[PushNotificationTool] Sending message: {message}")

        payload = {
            "user": pushover_user,
            "token": pushover_token,
            "message": message
        }
        requests.post(pushover_url, data=payload)
        return '{"notification": "ok"}'
