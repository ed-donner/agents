import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled


load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
OPENROUTER_API_BASE = (
    os.getenv("OPENROUTER_API_BASE")
    or os.getenv("OPENROUTER_BASE_URL")
    or os.getenv("OPENAI_BASE_URL")
    or "https://openrouter.ai/api/v1"
)


def configure_openai() -> None:
    if OPENROUTER_API_KEY:
        os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
    os.environ["OPENAI_BASE_URL"] = OPENROUTER_API_BASE

    set_default_openai_client(
        AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL"),
        )
    )
    set_default_openai_api("chat_completions")

    if "openrouter.ai" in (os.environ.get("OPENAI_BASE_URL") or ""):
        set_tracing_disabled(True)


configure_openai()

MODEL = os.getenv("MODEL", "openai/gpt-4o-mini")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
