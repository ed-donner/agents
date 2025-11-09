
from openai import AsyncOpenAI
from openai import OpenAI 
import os
from dotenv import load_dotenv 
load_dotenv(override=True) 
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1" 
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") 
client = AsyncOpenAI(base_url=ANTHROPIC_BASE_URL, api_key=ANTHROPIC_API_KEY) 
MODEL = "claude-haiku-4-5"

MAX_TOKENS = 200
TEMPERATURE = 0.3
