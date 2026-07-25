"""Application configuration — loads from .env file."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_openrouter_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key or key == "your_openrouter_api_key_here":
        raise ValueError("OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key.")
    return key


def get_model() -> str:
    return os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


def get_flask_secret() -> str:
    return os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")


def is_debug() -> bool:
    return os.getenv("FLASK_DEBUG", "false").lower() == "true"
