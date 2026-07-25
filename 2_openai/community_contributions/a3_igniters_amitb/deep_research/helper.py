from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1"
_MODEL = "gpt-4o-mini"

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_URL, api_key=OPENROUTER_API_KEY)

# import below variable to use in the agents to specify the model
AGENT_MODEL = OpenAIChatCompletionsModel(model=_MODEL, openai_client=openrouter_client)
