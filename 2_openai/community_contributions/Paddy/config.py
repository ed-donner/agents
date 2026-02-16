"""Gemini and OpenAI client config. Planner and writer use Gemini; search uses OpenAI (WebSearchTool)."""
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv(override=True)

# Avoid 400s from tracing backend (unknown parameter span_data.usage.total_tokens)
set_tracing_disabled(True)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Env for local; on Streamlit Cloud app.py injects st.secrets into os.environ before we're imported
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or ""

if GOOGLE_API_KEY:
    gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=GOOGLE_API_KEY)
    gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=gemini_client)
else:
    gemini_client = None
    gemini_model = None
