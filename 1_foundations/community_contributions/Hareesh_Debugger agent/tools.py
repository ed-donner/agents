import subprocess
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

def push_notification(message):
    """Sends a push notification to your phone."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": message,
        }
    )
    return "Notification sent."

def run_python_script(filename="sandbox.py"):
    """Runs the script and returns the result or traceback."""
    result = subprocess.run(["python", filename], capture_output=True, text=True)
    if result.returncode == 0:
        return f"SUCCESS! Output: {result.stdout}"
    return f"ERROR:\n{result.stderr}"

def write_to_file(code, filename="sandbox.py"):
    """Overwrites the sandbox file with new code."""
    with open(filename, "w") as f:
        f.write(code)
    return f"Updated {filename} successfully."

# The JSON Schemas for the Agent
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "run_python_script",
            "description": "Run the code and check for errors."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Edit the sandbox.py file.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "push_notification",
            "description": "Notify the user on their phone.",
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"]
            }
        }
    }
]