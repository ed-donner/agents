import os
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from dotenv import load_dotenv

load_dotenv(override=True)

# OpenRouter configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY"))

# Create OpenRouter client
openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# Create the model instance
mimo_model = OpenAIChatCompletionsModel(
    model="xiaomi/mimo-v2-flash:free",
    openai_client=openrouter_client
)
