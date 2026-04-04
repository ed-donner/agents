import os
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv(override=True)

BASE = "https://openrouter.ai/api/v1"
KEY = os.environ["OPENROUTER_API_KEY"]

INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "structured_output": True,
    "family": ModelFamily.UNKNOWN,
}

def gpt4o_mini_model(t=0.3):
    return OpenAIChatCompletionClient(
        model="openai/gpt-4o-mini",
        api_key=KEY, base_url=BASE, model_info=INFO, temperature=t,
    )

def haiku_model(t=0.7):
    return OpenAIChatCompletionClient(
        model="openai/gpt-4o-mini",
        # model="anthropic/claude-3.5-haiku"
        api_key=KEY, base_url=BASE, model_info=INFO, temperature=t,
    )

def grok_model(t=0.7):
    return OpenAIChatCompletionClient(
        model="x-ai/grok-3-mini",
        api_key=KEY, base_url=BASE, model_info=INFO, temperature=t,
    )

def sonnet_model(t=0.3):
    return OpenAIChatCompletionClient(
        # model="anthropic/claude-3.5-sonnet"
        model="openai/gpt-4o",
        api_key=KEY, base_url=BASE, model_info=INFO, temperature=t,
    )
