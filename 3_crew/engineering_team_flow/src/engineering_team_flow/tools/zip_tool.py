import os
import zipfile
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class ZipFolderInput(BaseModel):
    source_folder: str = Field(
        default="./output",
        description="Folder to zip (default: ./output)"
    )
    output_zip_path: str = Field(
        default="app.zip",
        description="Name of the zip file created inside the folder (default: app.zip)"
    )


class ZipFolderTool(BaseTool):
    name: str = "zip_folder"
    description: str = "Creates a ZIP file inside the folder, excluding the ZIP itself."
    args_schema: Type[BaseModel] = ZipFolderInput

    def _run(self, source_folder: str = "./output", output_zip_path: str = "app.zip") -> str:
        try:
            # Full absolute paths
            source_folder = os.path.abspath(source_folder)
            output_zip_path = os.path.join(source_folder, output_zip_path)
            output_zip_path = os.path.abspath(output_zip_path)

            if not os.path.isdir(source_folder):
                return f"Error: folder '{source_folder}' does not exist."

            # Ensure the zip file ends with .zip
            if not output_zip_path.endswith(".zip"):
                output_zip_path += ".zip"

            # Create zip
            with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_folder):
                    for file in files:
                        full_path = os.path.join(root, file)
                        # Skip the zip itself
                        if full_path == output_zip_path:
                            continue
                        arcname = os.path.relpath(full_path, source_folder)
                        zipf.write(full_path, arcname)

            return f"Zipped successfully: {output_zip_path}"

        except Exception as e:
            return f"Error while zipping folder: {str(e)}"