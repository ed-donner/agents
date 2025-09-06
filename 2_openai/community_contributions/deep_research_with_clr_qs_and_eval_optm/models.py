# models.py
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
import os

gemini_client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GEMINI_API_KEY"]
)

groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"]
)

gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
llama3_model = OpenAIChatCompletionsModel(model="meta-llama/llama-4-scout-17b-16e-instruct", openai_client=groq_client)