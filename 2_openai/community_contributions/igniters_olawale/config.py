import os
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel

# OpenRouter: base URL and API key (load_dotenv in deep_research.py loads repo-root .env)
_openrouter_client = AsyncOpenAI(
    base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
model = OpenAIChatCompletionsModel(
    model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    openai_client=_openrouter_client,
)
