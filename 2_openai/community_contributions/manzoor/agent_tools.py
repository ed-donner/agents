import json
import os
import base64
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

def save_structure(node):
    """
    Recursively creates directories and files from a JSON structure.
    """

    node_type = node.get("type")
    path = node.get("path")
    content = node.get("content")
    children = node.get("children", [])

    if node_type == "directory":
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Process children
        for child in children:
            save_structure(child)

    elif node_type == "file":
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Write file content
        with open(path, "w", encoding="utf-8") as f:
            if content is not None:
                f.write(content)