from typing import List
import os
from pydantic import BaseModel, Field
from typing import List,Type
from crewai.tools import BaseTool


class SaveFilesInput(BaseModel):
    """Information about files to save"""
    file_names: List[str] = Field(description="List of filenames to write")
    contents: List[str] = Field(description="List of text contents to save")
    output_directory: str = Field(description="Base directory for saving files")


class SaveFilesTool(BaseTool):
    """Tool for writing multiple files to disk"""

    name: str = "save_files"
    description: str = "Save multiple text files to disk in the specified directory."
    args_schema: Type[BaseModel] = SaveFilesInput

    def _run(self, file_names: List[str], contents: List[str], output_directory: str = "output") -> str:
        """Actually perform the file write operation"""
        os.makedirs(output_directory, exist_ok=True)

        saved_paths = []
        for name, content in zip(file_names, contents):
            file_path = os.path.join(output_directory, name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            saved_paths.append(file_path)

        return '{"File saved": "ok"}'