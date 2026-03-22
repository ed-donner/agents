from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    argument: str = Field(..., description="Placeholder — mini debate crew does not use tools.")


class MyCustomTool(BaseTool):
    name: str = "example_noop_tool"
    description: str = "Unused in this crew; kept for template parity with course debate project."

    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        return "noop"
