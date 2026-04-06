import os
from dotenv import load_dotenv
from agents.extensions.models.litellm_model import LitellmModel

load_dotenv(override=True)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

gpt_4o_mini_model = LitellmModel(
    model="openai/gpt-4o-mini",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=OPENROUTER_BASE_URL,
)
