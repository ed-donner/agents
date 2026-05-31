import requests


class PushOver:

    def __init__(self, config: dict) -> None:
        self.pushover_user = config.get("pushover_user")
        self.pushover_token = config.get("pushover_token")
        self.pushover_url = config.get("pushover_url")
    
        
    def push_notification(self, message: str) -> bool:

        push_notification_endpoint = self.pushover_url + '/messages.json'

        try:
            payload = {
                "user":  self.pushover_user,
                "token": self.pushover_token,
                "message": message
            }
            
            response = requests.post(push_notification_endpoint, data=payload, timeout=5)
            return response.status_code == 200
        
        except Exception as e:
            print(f"[ERROR] Push Notification error: {e}")
            return False