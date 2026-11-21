import asyncio

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    WebSearchTool,
    ModelSettings,
    function_tool,
)
from ddgs import DDGS
from dotenv import load_dotenv
import os

from openai import AsyncOpenAI

load_dotenv(override=True)

BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "openai/gpt-4o-mini")

openrouter_client = AsyncOpenAI(base_url=BASE_URL, api_key=OPENROUTER_API_KEY)
model = OpenAIChatCompletionsModel(openai_client=openrouter_client, model=MODEL_NAME)


INSTRUCTIONS = """
You are a research assistant. Given a search term, you search the web for that term and 
produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 words.
Capture the main points and be succinct. Reply only with the summary.
"""


@function_tool
async def MyWebSearchTool(query: str) -> str:
    """Ищет в интернете и возвращает заголовки, ссылки и краткие описания страниц.

    Args:
        query: Поисковый запрос на любом языке.
    """
    results = await asyncio.to_thread(DDGS().text, query, max_results=5)

    if not results:
        return f"По запросу {query!r} ничего не найдено."

    lines = []
    for number, item in enumerate(results, start=1):
        title = item.get("title") or "Без заголовка"
        url = item.get("href") or "Ссылка отсутствует"
        snippet = item.get("body") or "Описание отсутствует"
        lines.append(f"{number}. {title}\n   URL: {url}\n   Описание: {snippet}")

    return "\n\n".join(lines)


settings = ModelSettings(tool_choice="required")
tools = [MyWebSearchTool]

search_agent = Agent(
    name="Search Agent",
    instructions=INSTRUCTIONS,
    tools=tools,
    model=model,
    model_settings=settings,
)
