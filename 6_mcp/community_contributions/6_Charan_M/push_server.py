import os
from typing import Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"
sounds_url = "https://api.pushover.net/1/sounds.json"

def send_pushover_notification(
    message: str, 
    title: Optional[str] = None, 
    priority: int = 0, 
    url: Optional[str] = None,
    sound: Optional[str] = None
) -> str:
    """
    Send a push notification with a brief message using Pushover.
    
    Args:
        message: The main text of the notification.
        title: An optional title for the notification.
        priority: Priority of the message: -1 (low), 0 (normal), 1 (high).
        url: An optional URL to include with the message.
        sound: Optional sound name (e.g., 'magic', 'siren', 'echo'). Use list_notification_sounds to see all options.
    """
    print(f"Sending Pushover notification: {message}")
    
    if not pushover_user or not pushover_token:
        return "Error: PUSHOVER_USER or PUSHOVER_TOKEN missing in .env file."
        
    payload = {
        "user": pushover_user,
        "token": pushover_token,
        "message": message,
        "priority": priority
    }
    
    if title:
        payload["title"] = title
    if url:
        payload["url"] = url
    if sound:
        payload["sound"] = sound
    
    response = requests.post(pushover_url, data=payload)
    
    if response.status_code == 200:
        return f"Pushover notification successfully sent! Message: {message}"
    else:
        return f"Failed to send Pushover notification. Status code: {response.status_code}, Response: {response.text}"

def list_notification_sounds() -> str:
    """
    Retrieves the list of available notification sounds from Pushover.
    You can use these sound names in the 'sound' parameter of send_pushover_notification.
    """
    if not pushover_token:
        return "Error: PUSHOVER_TOKEN missing in .env file."
        
    response = requests.get(f"{sounds_url}?token={pushover_token}")
    
    if response.status_code == 200:
        sounds = response.json().get("sounds", {})
        sound_list = [f"- '{key}': {value}" for key, value in sounds.items()]
        return "Available Pushover sounds:\n" + "\n".join(sound_list)
    else:
        return f"Failed to fetch sounds. Status code: {response.status_code}"
