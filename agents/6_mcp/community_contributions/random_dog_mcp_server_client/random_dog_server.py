import requests
import json
from typing import Dict, Any
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("random_dog_server")

@mcp.tool()
async def get_random_dog() -> Dict[str, Any]:
    """Get a random dog image from the random.dog API.
    
    Returns:
        A dictionary containing the file size in bytes and URL of a random dog image
    """
    try:
        response = requests.get("https://random.dog/woof.json")
        response.raise_for_status()
        
        dog_data = response.json()
        
        return {
            "url": dog_data.get("url", ""),
            "fileSizeBytes": dog_data.get("fileSizeBytes", 0),
            "message": "Successfully retrieved random dog image!"
        }
    except requests.RequestException as e:
        return {
            "error": f"Failed to fetch random dog: {str(e)}",
            "url": "",
            "fileSizeBytes": 0
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse response: {str(e)}",
            "url": "",
            "fileSizeBytes": 0
        }

@mcp.tool()  
async def get_dog_image_url() -> str:
    """Get just the URL of a random dog image.
    
    Returns:
        The URL string of a random dog image
    """
    try:
        response = requests.get("https://random.dog/woof.json")
        response.raise_for_status()
        
        dog_data = response.json()
        return dog_data.get("url", "")
    except Exception as e:
        return f"Error fetching dog image: {str(e)}"

@mcp.resource("randomdog://image")
async def get_dog_resource() -> str:
    """Resource endpoint for getting random dog data"""
    try:
        response = requests.get("https://random.dog/woof.json")
        response.raise_for_status()
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run(transport="stdio") 