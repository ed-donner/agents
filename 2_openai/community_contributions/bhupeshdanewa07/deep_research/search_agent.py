from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, function_tool
from openai import AsyncOpenAI
from tavily import TavilyClient
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv(usecwd=True), override=True)

MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

gemini_model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=gemini_client
)

tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key)


@function_tool
def tavily_search(query: str) -> str:
    """
    Search the web for information using the Tavily Search API.
    
    Args:
        query: The search query string.
    """
    response = tavily_client.search(query=query, max_results=5)
    results = response.get("results", [])
    formatted = []
    for r in results:
        formatted.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}")
    return "\n---\n".join(formatted)


INSTRUCTIONS = """
You are a research assistant. Given a search term, you search the web for that term using your tool and 
produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 words.
Capture the main points and be succinct. Reply only with the summary.
"""

settings = ModelSettings(tool_choice="required")
tools = [tavily_search]

search_agent = Agent(name="Search Agent", instructions=INSTRUCTIONS, tools=tools, model=gemini_model, model_settings=settings)