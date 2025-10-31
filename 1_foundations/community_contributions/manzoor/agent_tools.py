from agents import function_tool
from typing import Any
import os
import json

@function_tool
def save_app_file_structure(filename, structure):
    """
    Save the final file structure so it can be used by other agents 
    to create the structure locally.
    
    Args: 
        filename (str): Path where the JSON should be saved (e.g, 'app_structure.json')
        json_structure (dict): The JSON structure to be saved
    """
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=4, ensure_ascii=False)
    print(f"JSON structure saved to {filename}")


@function_tool
def create_app_file_structure(filename, current_dir='.'):
    """
    Creates a file and directory structure locally based on JSON file.
    
    Args: 
        filename (str): Path to the JSON file 
        current_dir (str): Directory in which to create the structure
    """
    
    with open(filename, 'r', encoding='utf-8') as f:
        structure = json.load(f)

    def create_structure(structure_dict, base_path):
        """
        Recursively create directories and files.
        """
        for name, content in structure_dict.items():
            path = os.path.join(base_path, name)
            
            # it's a directory
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                print(f"Directory created: {path}")
                create_structure(content, path)  # Correct recursive call
            
            # it's a file
            else:
                os.makedirs(base_path, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"File created: {path}")

    create_structure(structure, current_dir)
    print("\nApp structure created successfully.")


@function_tool
def save_file_content(filename, file_path, extension, content):
    """
    Save any file content.
    
    Args:
        filename (str): Name of the file that needs to be saved 
        file_path (str): Directory where it should be saved
        extension (str): File extension (e.g, 'js', 'jsx') 
        content (str): The content to save 
    """
    os.makedirs(file_path, exist_ok=True)
    full_path = os.path.join(file_path, f"{filename}.{extension}")
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"File saved: {full_path}")
