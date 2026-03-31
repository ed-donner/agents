"""
LLM integration using OpenRouter for demand forecasting and agent reasoning.
"""
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def query_llm(prompt):
    if not OPENROUTER_API_KEY:
        logging.error("OpenRouter API key not set.")
        return "LLM error: API key not set."
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(f"{OPENROUTER_BASE_URL}/chat/completions", json=data, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        logging.error("LLM request timed out.")
        return "LLM error: request timed out."
    except Exception as e:
        logging.error(f"LLM error: {e}")
        return f"LLM error: {e}"
