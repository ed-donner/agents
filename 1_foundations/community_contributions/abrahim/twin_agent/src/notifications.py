import os
import requests
from dotenv import load_dotenv


class NotificationClient:
    def __init__(self):
        load_dotenv(override=True)
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.pushover_url = "https://api.pushover.net/1/messages.json"

        if self.pushover_user:
            if self.pushover_user.startswith("u"):
                print("Pushover user found and looks good")
            else:
                print("Pushover user found but doesn't start with u")
        else:
            print("Pushover user not found")

        if self.pushover_token:
            if self.pushover_token.startswith("a"):
                print("Pushover token found and looks good")
            else:
                print("Pushover token found but doesn't start with a")
        else:
            print("Pushover token not found")

    def push(self, message):
        print(f"Push: {message}")
        payload = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": message,
        }
        requests.post(self.pushover_url, data=payload)