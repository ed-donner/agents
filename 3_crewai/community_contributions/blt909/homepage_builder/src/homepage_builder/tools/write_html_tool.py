import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class WriteHtmlToolInput(BaseModel):
    """Input schema for WriteHtmlTool."""
    company_name: str = Field(..., description="The name of the company.")
    html_content: str = Field(..., description="The HTML content to write to the file.")
    is_amended: bool = Field(default=False, description="Whether this is an amended file after a review.")

class WriteHtmlTool(BaseTool):
    name: str = "Write HTML File Tool"
    description: str = (
        "Writes the given html_content to a file named after the company_name in the output folder. If is_amended is True, it appends _amended to the filename."
    )
    args_schema: Type[BaseModel] = WriteHtmlToolInput

    def _run(self, company_name: str, html_content: str, is_amended: bool = False) -> str:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filename = "".join(x for x in company_name.replace(' ', '_').lower() if x.isalnum() or x == '_')
        if is_amended:
            filename += "_amended"
        file_path = os.path.join(output_dir, f"{filename}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return f"File successfully written to {file_path}"
