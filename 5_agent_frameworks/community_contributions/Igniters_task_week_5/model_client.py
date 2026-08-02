import os

from dotenv import load_dotenv
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ENV_FILE = os.path.join(CURRENT_DIR, ".env")
REPO_ENV_FILE = os.path.join(os.path.dirname(CURRENT_DIR), ".env")

load_dotenv(PROJECT_ENV_FILE, override=True)
load_dotenv(REPO_ENV_FILE, override=False)

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")


def build_openrouter_client(*, temperature: float = 0.3, response_format=None, model: str | None = None):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. Add it to your shell or .env before running the app."
        )

    config = {
        "model": model or DEFAULT_OPENROUTER_MODEL,
        "api_key": api_key,
        "base_url": OPENROUTER_BASE_URL,
        "temperature": temperature,
        "model_info": ModelInfo(
            vision=False,
            function_calling=False,
            json_output=True,
            family="openai",
            structured_output=True,
        ),
    }
    if response_format is not None:
        config["response_format"] = response_format
    return OpenAIChatCompletionClient(**config)
