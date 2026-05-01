from pydantic import BaseModel
from utilities.settings import Settings
import requests
import json


class Notification:
    

    def __init__(self):
        
        self.settings = Settings()
        
 
    
    def pushover(self, message: str):
        payload = {
            "user": self.settings.pushover_user_key,
            "token": self.settings.pushover_app_token,
            "message": message
        }
        requests.post(self.settings.pushover_url, data=payload)
    
    def send_email(self, message: str, subject: str):
        print(f"Sending email to {self.settings.mailgun_recipient} with subject {subject} and message {message}")
        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{self.settings.mailgun_domain}/messages",
                auth=("api", self.settings.mailgun_api_key),
                data={
                    "from": self.settings.mailgun_from_email,
                    "to": self.settings.mailgun_recipient,
                    "subject": subject,
                    "text": message
                }
            )

            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")

            if response.status_code == 200:
                return json.dumps({"status": "success", "message": "Email sent successfully"})
            else:
                return json.dumps({"status": "error", "code": response.status_code, "message": response.text})

        except Exception as e:
            print(f"Error sending email: {e}")
            return json.dumps({"status": "error", "message": str(e)})