import json
import os
from pathlib import Path
from typing import Annotated, Dict, Any
from agents import function_tool

app_directory = "app"

@function_tool
def save_files(structure: dict, base_folder = f"{app_directory}"):
    
    """
    Creates directories and files based on the provided structure.
    Args:
        structure (dict): A dictionary representing the file structure.
        base_folder (str): The base folder where the structure will be created.
    
    Returns:
        Dict with 'success', 'files_created', and 'errors' keys.
    """

    # Check if structure is dict 
    if not isinstance(structure, dict):
        # If it's a string, try to parse it as JSON
        try:
            structure = json.loads(structure)
        except json.JSONDecodeError as e:
            print(f"Error parsing structure: {e}")
            return  
        
    def process(structure):
        if not isinstance(structure, dict):
            return
        
        # Is this a file?
        if 'path' in structure and 'content' in structure:
            try:
                file_path = Path(base_folder) / structure['path']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(structure['content'] or "", encoding='utf-8')
        
                print(f"Created file: {file_path}\n")
                print(f"Content:\n {structure['content']}\n")
            
            except Exception as e:
                print(f"Error creating file {structure['path']}: {e}")
        else:
            for value in structure.values():
                process(value)

    process(structure)

@function_tool 
def save_database_content(schema: str): 
    
    """
    Saves the database schema to a specified file.
    
    Args:
        schema (str): The database schema as a text string.
        output_path (str): The file path where the database schema will be saved.
    """ 
    database_dir = os.path.join(os.getcwd(), app_directory, "database")
    database_file = os.path.join(database_dir, "schema.db")
    
    os.makedirs(database_dir, exist_ok=True)
    
    with open(database_file, 'w', encoding='utf-8') as f:
        f.write(schema)
        print(f"Database schema saved to {database_file}")
