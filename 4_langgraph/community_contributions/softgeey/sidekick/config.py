"""Central configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value


class Config:
    # LLM
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    # Research
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Google
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE: str = "token.json"
    GOOGLE_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]

    # App server
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    def validate(self) -> None:
        """Raise if critical keys are missing."""
        if not self.OPENROUTER_API_KEY:
            raise EnvironmentError("OPENROUTER_API_KEY is not set in .env")


config = Config()
