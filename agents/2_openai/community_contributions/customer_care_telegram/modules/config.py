from dataclasses import dataclass
from typing import Optional
import os

# --- Configuration ---
@dataclass
class Config:
    TELEGRAM_API_TOKEN: str = os.getenv("TELEGRAM_API_TOKEN", "")
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    PORT: int = int(os.environ.get("PORT", 4000))
    APP_NAME: str = "ecommerce_bot_app"
    ROOT_AGENT_NAME: str = "ecommerce_salesman_v1"
    ROOT_AGENT_MODEL: str = "gemini-2.0-flash-exp"
    CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

    def validate(self):
        if not self.TELEGRAM_API_TOKEN:
            raise ValueError("TELEGRAM_API_TOKEN must be set in environment variables")
        if not os.path.exists(self.CREDENTIALS_PATH):
            raise ValueError(f"Google credentials file not found at {self.CREDENTIALS_PATH}")