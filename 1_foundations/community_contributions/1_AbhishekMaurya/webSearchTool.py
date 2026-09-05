from agents import Agent, function_tool, ModelSettings,OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
import requests
load_dotenv(override=True)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
google_api_key = os.getenv("GOOGLE_API_KEY")
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-3.5-flash-lite", openai_client=gemini_client)
MODEL_NAME = gemini_model



@function_tool
def web_search(query: str) -> str:

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": os.environ["SERPER_API_KEY"],
        "Content-Type": "application/json"
    }

    payload = {
        "q": query
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("organic", [])

    if not results:
        return "No search results found."

    output = []

    for result in results[:5]:

        title = result.get("title", "")
        link = result.get("link", "")
        snippet = result.get("snippet", "")

        output.append(
            f"Title: {title}\n"
            f"URL: {link}\n"
            f"Snippet: {snippet}"
        )

    return "\n\n---\n\n".join(output)

INSTRUCTIONS = """
You are a research assistant. Given a search term, you search the web for that term and 
produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 words.
Capture the main points and be succinct. Reply only with the summary.
"""

settings = ModelSettings(tool_choice="required")
tools = [web_search]

search_agent = Agent(name="Search Agent", instructions=INSTRUCTIONS, tools=tools, model=MODEL_NAME, model_settings=settings)