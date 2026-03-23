from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class PushNotification(BaseModel):
    """A message to be sent to the user"""
    message: str = Field(..., description="The message to be sent to the user.")

class PushNotificationTool(BaseTool):
    name: str = "Send a Push Notification"
    description: str = (
        "This tool is used to send a push notification to the user. It is mandatory to use it."
    )
    args_schema: Type[BaseModel] = PushNotification

    def _run(self, message: str) -> str:
        load_dotenv(override=True)
        print("push token: ", os.getenv("PUSHOVER_USER_KEY"))
        print("============,,,,,,,....>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        pushover_user = os.getenv("PUSHOVER_USER_KEY")
        pushover_token = os.getenv("PUSHOVER_TOKEN")
        pushover_url = "https://api.pushover.net/1/messages.json"

        print(f"Push: {message}")
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        requests.post(pushover_url, data=payload)
        return '{"notification": "ok"}'




# if __name__ == "__main__":
#     print("token: ", os.getenv("PUSHOVER_USER_KEY"))
#     message = "Tests"
#     pushover_user = os.getenv("PUSHOVER_USER_KEY")
#     pushover_token = os.getenv("PUSHOVER_TOKEN")
#     pushover_url = "https://api.pushover.net/1/messages.json"

#     print(f"Push: {message}")
#     payload = {"user": pushover_user, "token": pushover_token, "message": message}
#     requests.post(pushover_url, data=payload)