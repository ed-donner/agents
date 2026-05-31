import requests
from typing import Optional


class PushoverNotifier:
    
    def __init__(self, user_key: str, app_token: str, url: str = "https://api.pushover.net/1/messages.json"):
        self.user_key = user_key
        self.app_token = app_token
        self.url = url
        self.enabled = bool(user_key and app_token)
    
    def send(self, message: str, title: Optional[str] = None) -> bool:
        if not self.enabled:
            print(f"[PUSH DISABLED] {message}")
            return False
        
        print(f"[PUSH] {message}")
        try:
            payload = {
                "user": self.user_key,
                "token": self.app_token,
                "message": message
            }
            if title:
                payload["title"] = title
            
            response = requests.post(self.url, data=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Push notification failed: {e}")
            return False

