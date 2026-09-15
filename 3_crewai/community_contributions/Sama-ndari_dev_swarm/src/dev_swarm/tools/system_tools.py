import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class FileWriteInput(BaseModel):
    path: str = Field(..., description="The name of the file to save (e.g., 'server.py').")
    content: str = Field(..., description="The code or text content to save.")

class AdvancedFileWriterTool(BaseTool):
    name: str = "Advanced FileWriter"
    description: str = "Mandatory tool for saving code. It forces files into the project_output/src directory."
    args_schema: type[BaseModel] = FileWriteInput

    def _run(self, path: str, content: str) -> str:
        try:
            # 1. Clean the filename (remove any directories the AI tried to prepend)
            filename = os.path.basename(path)
            if not filename:
                return "❌ ERROR: No filename provided."

            # 2. Define the absolute safe path
            base_dir = os.path.join(os.getcwd(), "project_output", "src")
            safe_path = os.path.join(base_dir, filename)
            
            # 3. Ensure the folder exists
            os.makedirs(base_dir, exist_ok=True)
            
            with open(safe_path, "w") as f:
                f.write(content)
            
            return f"✅ SUCCESS: File saved correctly to safe zone at: {safe_path}"
        
        except Exception as e:
            return f"❌ ERROR: System failed to write file. {str(e)}"