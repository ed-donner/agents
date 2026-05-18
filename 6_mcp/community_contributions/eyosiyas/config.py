import os
from dotenv import load_dotenv

# Load your OpenAI API key here or from environment variables
load_dotenv(override=True)
OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")