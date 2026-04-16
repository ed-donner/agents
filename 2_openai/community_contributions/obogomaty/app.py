import os
from dotenv import load_dotenv
import openai
import gradio as gr
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

load_dotenv()

SYSTEM_PROMPT = "You are a deep research assistant. Answer with detailed, well-sourced information."


client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
)

def research_chat(user_message, history):

    # Input guardrail: check for empty or too long input
    if not user_message or not isinstance(user_message, str) or len(user_message.strip()) == 0:
        return "Please enter a valid research question."
    if len(user_message) > 1000:
        return "Your question is too long. Please shorten it to under 1000 characters."

    # Prompt injection filter: block common attack patterns
    injection_patterns = [
        r"ignore (all|any|the)? ?previous instructions?",
        r"disregard (all|any|the)? ?previous instructions?",
        r"pretend (to be|you are)",
        r"you are now",
        r"as an ai language model",
        r"repeat after me",
        r"do anything now",
        r"bypass",
        r"jailbreak",
        r"forget all previous",
        r"act as",
        r"system prompt",
        r"/system",
        r"### system",
        r"assistant:"
    ]
    import re
    for pattern in injection_patterns:
