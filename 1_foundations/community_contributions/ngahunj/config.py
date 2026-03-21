import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

BASE_URL = "https://openrouter.ai/api/v1"

CHAT_MODEL = "z-ai/glm-4.5-air:free"
EVAL_MODEL = "openai/gpt-oss-120b:free"

EVALUATION_MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
