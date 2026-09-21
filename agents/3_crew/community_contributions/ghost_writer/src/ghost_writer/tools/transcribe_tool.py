from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class TranscribeToolInput(BaseModel):
    content: str = Field(..., description="Content to append to the file.")

class TranscribeTool(BaseTool):
    name: str = "AppendTool"
    description: str = "Appends content to a specified text file."
    args_schema: Type[BaseModel] = TranscribeToolInput
    filename: str = "output/book.md" 

    def _run(self, content: str) -> str:
        try:
            with open(self.filename, 'a', encoding='utf-8') as file:
                file.write(content + '\n')
            return f"Content appended to {self.filename}."
        except Exception as e:
            return f"Failed to append to {self.filename}: {e}"
