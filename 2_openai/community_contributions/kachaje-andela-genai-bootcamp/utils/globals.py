from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from .logger import trace, gen_trace_id, span
from tools.web_search import web_search

OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama_client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
ollama_model = OpenAIChatCompletionsModel(model="llama3.2", openai_client=ollama_client)
