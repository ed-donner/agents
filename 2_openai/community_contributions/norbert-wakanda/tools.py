import os
import time
import json
from datetime import datetime
from agents import function_tool
import requests
from dotenv import load_dotenv
load_dotenv(override=True)

from typing import List, Dict

linked_in_post_api_key = os.getenv('LINKEDIN_POST_API_KEY')

MAX_CONT = 1000


@function_tool
def get_recent_files_context(directory:str=".", hours:int  =24)->List[Dict]:
    "Function to get the files modified by the user in the last 24 hours and return the content"

    allowed_extensions = (".py")
    recent_files = []
    cutoff_time = time.time() - hours * 3600

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(allowed_extensions):
                continue

            path = os.path.join(root, file)

            try:
                modified_time = os.path.getmtime(path)

                if modified_time < cutoff_time:
                    continue

                # Read file content
                if file.endswith(".py"):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                elif file.endswith(".ipynb"):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        notebook = json.load(f)

                    code_cells = []
                    for cell in notebook.get("cells", []):
                        if cell.get("cell_type") == "code":
                            code_cells.append("".join(cell.get("source", [])))

                    content = "\n\n".join(code_cells)

                # Limit context size
                content = content[:MAX_CONT]

                recent_files.append({
                    "file": path,
                    "modified_time": modified_time,
                    "content": content
                })

            except Exception as e:
                print("  Skipped:", path, "| Error:", str(e))
    return recent_files


@function_tool
def post_to_linkedin(post: str) -> dict:
    """
    Posts the given text to your personal LinkedIn profile via Upload-Post API.
    Uses your fixed username: nober1
    
    Returns the API response on success.
    Raises an exception with details on failure.
    """
    API_KEY = linked_in_post_api_key       # ← Replace this with your real API key
    USERNAME = "nober1"                     # Your confirmed username
    
    url = "https://api.upload-post.com/api/upload_text"
    
    headers = {
        "Authorization": f"Apikey {API_KEY}"
    }
    
    data = {
        "user": USERNAME,
        "platform[]": "linkedin",
        "title": post                         # This becomes the full post body on LinkedIn
    }
    
    response = requests.post(url, headers=headers, data=data, timeout=20)
    response.raise_for_status()                 # Raises if HTTP error (e.g. 401, 400)
    
    result = response.json()
    
    if not result.get("success", False):
        error_msg = result.get("message") or result.get("error") or "Unknown error"
        raise ValueError(f"Upload-Post API failed: {error_msg}")
    
    # Optional: Print success info (LinkedIn post URL if immediately available)
    if "results" in result and "linkedin" in result["results"]:
        linkedin_info = result["results"]["linkedin"]
        if "url" in linkedin_info:
            print(f"Posted successfully! View on LinkedIn: {linkedin_info['url']}")
    
    return result