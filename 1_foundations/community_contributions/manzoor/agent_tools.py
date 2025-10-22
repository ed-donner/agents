from agents import function_tool
import os 
import json 

# Save / modify the app file structure
@function_tool 
def save_app_file_structure(filename:str, json_structure:dict):
    """ 
    Save the final file structure so it can be used by other agents to 
    create the structure locally.
    
    Args: 
        filename (str): The path where the JSON should be saved (e.g, 'app_structure.json')
        json_structure (dict): The JSON structure to be saved
    """    
    
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_structure, f, indent=4, ensure_ascii=False)
        
@function_tool
def create_app_file_structure(filename, current_dir='.'):
    """
    Creates a file and directory structure locally based on final 
    JSON 
    
    Args: 
        filename (str): Path to the JSON file 
        current_dir (str): Directory in which to create the structure
    """
    
    # Load the JSON structure 
    with open(filename, 'r') as f:
        structure = json.loads(f)
    
    def create_structure(structure, base_path):
        """ Recursively create directories and files

        Args: 
            structure: (json) JSON structure file 
            base_path: (str) the directory
        """
        
        for name, content in structure.items():
            path = os.path.join(base_path, name)

            # If content is a dict, it'a a directory
            if isinstance(content, dict):
                if not os.path.exists(path):
                    os.makedirs(path)
                    print(f"Directory created: {path}")
                else:
                    print(f"Directory already exists: {path}")
                create_app_file_structure(content, path)
            
            # If content is a string, it's a file 
            else:
                # Ensure directory exists 
                os.makedirs(base_path, exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content)
                print(f"File created: {path}")

    create_app_file_structure(structure, current_dir)
    print("\n App structure created successfully.")

