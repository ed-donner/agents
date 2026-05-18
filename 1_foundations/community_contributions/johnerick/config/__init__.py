import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import chromadb
from chromadb.config import Settings

load_dotenv(override=True)

class Config:
    def __init__(self):
        # OpenRouter / OpenAI setup
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_api_key
        )

        # Pushover setup
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        if not self.pushover_user or not self.pushover_token:
            raise ValueError("PUSHOVER_USER or PUSHOVER_TOKEN not set in environment")
        
        # Chroma DB setup
        self.chroma_persist_dir = "./chroma_db"
        self.chroma_client = chromadb.PersistentClient(self.chroma_persist_dir)
        self.career_collection = self.chroma_client.get_or_create_collection(name="career_docs")

    def send_push_notification(self, message: str, title: str = "Career Agent"):
        """
        Send a push notification via Pushover.
        """
        payload = {
            "token": self.pushover_token,
            "user": self.pushover_user,
            "message": message,
            "title": title,
            "timestamp": int(datetime.now().timestamp())
        }
        response = requests.post(self.pushover_url, data=payload)
        response.raise_for_status()
        return response.json()

    def get_config_dict(self):
        """
        Return a dictionary representation of the configuration.
        """
        return {
            "openai": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": self.openrouter_api_key
            },
            "pushover": {
                "user": self.pushover_user,
                "token": self.pushover_token,
                "url": self.pushover_url
            }
        }
