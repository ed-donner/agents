import json
import os
import base64
from typing import Union
from pathlib import Path
from agents import function_tool

@function_tool
def save_source_code(json_source: str) -> str:
    """ Save the JSON structure"""
    
    app_source_code_file = "app_code.json"
    content = json.dumps(json_source, separators=(',', ":"), indent=4)
    
    with open(app_source_code_file, 'w', encoding="utf-8") as f:
        f.write(content)
    print(f"App source code saved to {app_source_code_file}")
    
    return f"App source code saved to {app_source_code_file}"

@function_tool
def save_database_content(database_schema: str):
    """
    Saves the database schema to ./schema.db
    """
    database_file = "schema.db"
    
    with open(database_file, 'w', encoding='utf-8') as f:
        f.writelines(database_schema)

    return f"Database schema saved successfully to {database_file}"

def write_structure(node):
    """
    Recursively write files and directories
    
    node: dict with key file_name, type, path, content, children (optional)
    """
    node_type = node.get("type")
    path = node.get("path")
    
    if node_type == "directory":
        # Create directory
        Path(path).mkdir(parents=True, exist_ok=True)
        
        # Process children
        for child in node.get("children", []):
            write_structure(child)
    
    elif node_type == "file":
        # Ensure parent directory exists 
        parent_dir = os.path.dirname(path)
        if parent_dir:
            Path(parent_dir).mkdir(parents=True, exist_ok=True)
        
        # Decode base64 content and write file 
        content_base64 = node.get("content", "")
        content = base64.b64decode(content_base64.encode("utf-8")).decode("utf-8")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created file :{path}")
    else:
        raise ValueError(f"Unknown node type: {node_type}")

if __name__ == "__name__":
    pass