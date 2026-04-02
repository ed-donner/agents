from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os


load_dotenv(override=True)

set_tracing_disabled(True)

openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = 'https://openrouter.ai/api/v1'

openrouter = AsyncOpenAI(api_key=openrouter_key, base_url= openrouter_url)

model_client = OpenAIChatCompletionsModel(model= 'gpt-4.1-mini', openai_client=openrouter)