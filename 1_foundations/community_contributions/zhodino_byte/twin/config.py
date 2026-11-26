import os

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.4-mini")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
OWNER_REPLY_TIMEOUT_SECONDS = int(os.getenv("OWNER_REPLY_TIMEOUT_SECONDS", "120"))


def validate_settings() -> None:
    required = {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {names}")
    if OWNER_REPLY_TIMEOUT_SECONDS <= 0:
        raise RuntimeError("OWNER_REPLY_TIMEOUT_SECONDS must be greater than zero")
