"""Gemini and OpenAI client config. Planner and writer use Gemini; search uses OpenAI (WebSearchTool)."""
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv(override=True)

# Avoid 400s from tracing backend (unknown parameter span_data.usage.total_tokens)
set_tracing_disabled(True)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Env for local; Streamlit Cloud uses Secrets (st.secrets), not always set as env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
try:
    import streamlit as st
    if not GOOGLE_API_KEY:
        GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY") or ""
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or ""
        if OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
except Exception:
    pass
if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not set. Use .env locally, or on Streamlit Cloud: "
        "Manage app → Settings → Secrets (add GOOGLE_API_KEY and OPENAI_API_KEY)."
    )

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=GOOGLE_API_KEY)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=gemini_client)
