import os
import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
api_base = "https://openrouter.ai/api/v1"
headers = {"Authorization": f"Bearer {api_key}"}

resp = httpx.get(f"{api_base}/models", headers=headers)
print("Available models:")
print(resp.text)
