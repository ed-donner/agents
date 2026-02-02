from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class NotificationInput(BaseModel):
    message: str = Field(..., description="Notification message to send")


class NotificationTool(BaseTool):
    name: str = "Notification Tool"
    description: str = "Sends notifications or alerts to the user."
    args_schema: Type[BaseModel] = NotificationInput

    def _run(self, message: str) -> str:
        formatted = f"NOTIFICATION: {message}"
        print(formatted)
        return formatted




