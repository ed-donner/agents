import os
from openai import AsyncOpenAI
from agents import Agent, function_tool, ModelSettings, OpenAIChatCompletionsModel
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "claude-haiku-4-5-20251001")
USE_EMAIL = True
HOW_MANY_SEARCHES = 5


anthropic_client = AsyncOpenAI(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)

anthropic_model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=anthropic_client,
)
