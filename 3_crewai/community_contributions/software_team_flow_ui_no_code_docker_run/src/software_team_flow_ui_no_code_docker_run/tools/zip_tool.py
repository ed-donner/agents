from pathlib import Path
import zipfile
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class ZipFolderInput(BaseModel):
    source_folder: str = Field(
        default="./output/app",
        description="Folder to zip (default: ./output/app)"
    )
    output_zip_path: str = Field(
        default="./output/zip/app.zip",
        description="Full path and name of the zip file to be created (default: ./output/zip/app.zip)"
    )
    compress_level: int = Field(
        default=9,
        description="The compression level to use (0=no compression, 9=best compression for ZIP_DEFLATED). Default is 9."
    )


class ZipFolderTool(BaseTool):
    name: str = "zip_folder"
    description: str = "Creates a ZIP file of the source folder, ensuring the zip is placed at the specified output_zip_path."
    args_schema: Type[BaseModel] = ZipFolderInput

    def _run(self, source_folder: str = "./output/app", output_zip_path: str = "./output/zip/app.zip", compress_level: int = 9) -> bool:
        """
        Creates a ZIP archive of the specified source folder.

        The key fix here is using file_path.relative_to(source_path) for arcname, 
        which ensures the zipped content is placed at the root of the archive 
        (avoiding an extra 'app' folder inside the zip).
        
        Now includes 'compress_level' for better control over the compression ratio.
        """
        try:
            # Resolve paths relative to the current working directory (Path.cwd()) for robustness
            source_path = (Path.cwd() / source_folder).resolve()
            zip_path = (Path.cwd() / output_zip_path).resolve()

            # 1. Validation
            if not source_path.is_dir():
                print(f"[ZipFolderTool] Error: Source folder not found at {source_path}")
                return False

            # 2. Ensure Output Directory Exists
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 3. Perform Zipping
            # Added compresslevel to the constructor
            with zipfile.ZipFile(
                zip_path, 
                "w", 
                zipfile.ZIP_DEFLATED, 
                compresslevel=compress_level,
                strict_timestamps=True # Default is True, added for clarity/future modification
            ) as zipf:
                files_zipped_count = 0
                
                # Recursively iterate through all files and folders in the source directory
                # Use os.walk alternative for large directories, but rglob is fine for most app structures.
                for file_path in source_path.rglob("*"):
                    # Only add standard files to the zip archive, and skip symbolic links
                    if file_path.is_file() and not file_path.is_symlink():
                        # CRITICAL: arcname defines the path *inside* the zip file.
                        # Using relative_to ensures the files are rooted in the zip, 
                        # not buried under the absolute path.
                        zipf.write(file_path, arcname=file_path.relative_to(source_path))
                        files_zipped_count += 1
                    # Skip directories, symlinks, and other special files
                    
            if files_zipped_count == 0:
                print(f"[ZipFolderTool] Warning: Created a zip file with 0 contents from {source_path}. Check if the CrewAI flow successfully wrote files.")
                # We still return True if the zip file itself was created (even if empty)
            else:
                print(f"Zip file created with {files_zipped_count} files.")
                
            print(f"Successfully created zip file at: {zip_path}")
            return True

        except Exception as e:
            print(f"[ZipFolderTool] Error: Failed to create zip: {e}")
            return False