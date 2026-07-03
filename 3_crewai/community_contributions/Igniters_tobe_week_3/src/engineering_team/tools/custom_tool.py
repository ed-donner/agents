from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CustomToolInput(BaseModel):
    argument: str = Field(...)


class CustomTool(BaseTool):
    name: str = "custom_tool"
    description: str = "Placeholder tool."
    args_schema: Type[BaseModel] = CustomToolInput

    def _run(self, argument: str) -> str:
        return argument
