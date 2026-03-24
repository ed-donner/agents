from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import os


class ReplyTrackerInput(BaseModel):
    investor_email: str = Field(..., description="Investor email")
    reply_message: str = Field(..., description="Reply from investor")


class ReplyTrackerTool(BaseTool):
    name: str = "Reply Tracker Tool"
    description: str = "Tracks investor responses."
    args_schema: Type[BaseModel] = ReplyTrackerInput

    def _run(self, investor_email: str, reply_message: str) -> str:
        file_path = "logs/replies.json"

        data = []

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)

        data.append({
            "investor": investor_email,
            "reply": reply_message
        })

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        return f"Reply recorded for {investor_email}"