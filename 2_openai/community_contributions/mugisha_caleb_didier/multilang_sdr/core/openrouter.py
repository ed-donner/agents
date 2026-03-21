import os

from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def make_openrouter_model(model_id: str) -> OpenAIChatCompletionsModel:
    client = AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    return OpenAIChatCompletionsModel(model=model_id, openai_client=client)
