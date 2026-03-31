import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE") or "https://openrouter.ai/api/v1"

if OPENROUTER_API_KEY and not OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
    os.environ.setdefault("OPENAI_BASE_URL", OPENROUTER_API_BASE)
elif OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    if OPENAI_BASE_URL:
        os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL

MODEL = os.getenv("MODEL", "openai/gpt-4o-mini")
ENABLE_BROWSER = os.getenv("ENABLE_BROWSER", "false").lower() in {"1", "true", "yes"}
