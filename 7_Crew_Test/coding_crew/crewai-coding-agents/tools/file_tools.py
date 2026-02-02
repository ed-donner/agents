"""
File system operation tools for agents
"""
import os
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool
from config.settings import settings


class FileWriterInput(BaseModel):
    """Input schema for file writing"""
    file_path: str = Field(..., description="Path to the file (relative to output directory)")
    content: str = Field(..., description="Content to write to the file")
    overwrite: bool = Field(default=True, description="Overwrite if file exists")


class FileWriterTool(BaseTool):
    name: str = "File Writer Tool"
    description: str = """
    Writes content to a file in the output directory.
    Creates directories if they don't exist.
    Use this tool to save generated code, configs, or documentation.
    """
    args_schema: Type[BaseModel] = FileWriterInput
    
    def _run(self, file_path: str, content: str, overwrite: bool = True) -> str:
        """Write content to file"""
        full_path = os.path.join(settings.output_dir, file_path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Check if file exists
        if os.path.exists(full_path) and not overwrite:
            return f"❌ File already exists: {file_path}"
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ File written successfully: {file_path}"


class FileReaderInput(BaseModel):
    """Input schema for file reading"""
    file_path: str = Field(..., description="Path to the file to read")


class FileReaderTool(BaseTool):
    name: str = "File Reader Tool"
    description: str = """
    Reads content from a file.
    Use this tool to read existing code or configuration files.
    """
    args_schema: Type[BaseModel] = FileReaderInput
    
    def _run(self, file_path: str) -> str:
        """Read content from file"""
        # Try output directory first, then absolute path
        paths_to_try = [
            os.path.join(settings.output_dir, file_path),
            file_path
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return f"❌ File not found: {file_path}"


class DirectoryInput(BaseModel):
    """Input schema for directory operations"""
    path: str = Field(..., description="Directory path")
    operation: str = Field(
        default="list",
        description="Operation to perform (list, create, delete)"
    )


class DirectoryTool(BaseTool):
    name: str = "Directory Tool"
    description: str = """
    Performs directory operations like listing, creating, or managing directories.
    Use this tool to organize project structure.
    """
    args_schema: Type[BaseModel] = DirectoryInput
    
    def _run(self, path: str, operation: str = "list") -> str:
        """Perform directory operation"""
        full_path = os.path.join(settings.output_dir, path)
        
        if operation == "list":
            if not os.path.exists(full_path):
                return f"❌ Directory not found: {path}"
            
            items = os.listdir(full_path)
            return "\n".join([f"📁 {item}" if os.path.isdir(os.path.join(full_path, item)) 
                            else f"📄 {item}" for item in items])
        
        elif operation == "create":
            os.makedirs(full_path, exist_ok=True)
            return f"✅ Directory created: {path}"
        
        elif operation == "delete":
            if os.path.exists(full_path):
                import shutil
                shutil.rmtree(full_path)
                return f"✅ Directory deleted: {path}"
            return f"❌ Directory not found: {path}"
        
        return f"❌ Unknown operation: {operation}"
