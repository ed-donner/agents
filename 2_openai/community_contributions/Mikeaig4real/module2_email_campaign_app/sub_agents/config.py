"""
Configuration module for the email campaign application.
This module loads environment variables and exports API keys.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

print("OPENAI_API_KEY set:", bool(openai_api_key))
print("GOOGLE_API_KEY set:", bool(google_api_key))
print("DEEPSEEK_API_KEY set:", bool(deepseek_api_key))
print("GROQ_API_KEY set:", bool(groq_api_key))
print("OPENROUTER_KEY set:", bool(openrouter_api_key))