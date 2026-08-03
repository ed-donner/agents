import os
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class PushInput(BaseModel):
    message: str = Field(..., description="The message to send to the user.")

class PushNotificationTool(BaseTool):
    name: str = "Push Notification Tool"
    description: str = "Sends a real-time push notification to the user's phone via Pushover."
    args_schema: type[BaseModel] = PushInput

    def _run(self, message: str) -> str:
        user = os.getenv("PUSHOVER_USER")
        token = os.getenv("PUSHOVER_TOKEN")
        
        if not user or not token:
            print(f"\n🔔 [MOCK NOTIFICATION SENT]: {message}\n")
            return "Notification logged to console (Mock Mode)."
        # -------------------------------------------------
            
        url = "https://api.pushover.net/1/messages.json"
        data = {"user": user, "token": token, "message": message}
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                return "Notification sent successfully."
            return f"Failed to send notification. Status: {response.status_code}"
        except Exception as e:
            return f"Error sending notification: {str(e)}"