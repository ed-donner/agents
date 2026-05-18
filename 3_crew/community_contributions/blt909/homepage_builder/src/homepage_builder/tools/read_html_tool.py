import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class ReadHtmlToolInput(BaseModel):
    """Input schema for ReadHtmlTool."""
    company_name: str = Field(..., description="The name of the company.")

class ReadHtmlTool(BaseTool):
    name: str = "Read HTML File Tool"
    description: str = (
        "Reads the HTML file of the given company_name from the output folder and returns its content."
    )
    args_schema: Type[BaseModel] = ReadHtmlToolInput

    def _run(self, company_name: str) -> str:
        output_dir = "output"
        filename = "".join(x for x in company_name.replace(' ', '_').lower() if x.isalnum() or x == '_')
        file_path = os.path.join(output_dir, f"{filename}.html")
        
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist."
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
