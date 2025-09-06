import os
import sys
from typing import Dict, Literal

from pydantic import BaseModel

# from loguru import logger


# --- LLM Configuration ---
class LLMConfig(BaseModel):
    """Configuration for a single LLM provider."""

    model_name: str
    base_url: str
    # Specify which environment variable holds the API key.
    # This allows us to have one generic function to create clients.
    api_key_env_var: str


# This is a static registry of available models, not a dynamic setting.
# A simple dictionary is much clearer and more appropriate than a Pydantic Settings class.
AVAILABLE_LLMS: Dict[str, LLMConfig] = {
    "gemini": LLMConfig(
        model_name="gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env_var="GOOGLE_API_KEY",
    ),
    "deepseek": LLMConfig(
        model_name="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key_env_var="DEEPSEEK_API_KEY",
    ),
    "groq": LLMConfig(
        model_name="meta-llama/llama-4-scout-17b-16e-instruct",  # Updated model name
        base_url="https://api.groq.com/openai/v1",
        api_key_env_var="GROQ_API_KEY",
    ),
    # To add a new provider, you just add an entry here. No other code changes needed!
    # "another_provider": LLMConfig(
    #     model_name="some-model",
    #     base_url="https://api.another.com/v1",
    #     api_key_env_var="ANOTHER_API_KEY",
    # ),
}

# Dynamically create a Literal type from the keys of our registry.
# This ensures that any code using this type is always in sync with our available LLMs.
LLMProvider = Literal[*AVAILABLE_LLMS.keys()]


class CurriculumCheckOutput(BaseModel):
    good_quality: bool
    matches_goal: bool


# # --- Logger Setup ---
# def setup_logging() -> None:
#     """Configures the Loguru logger for the application."""
#     LOG_FORMAT = (
#         "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
#         "<level>{level: <8}</level> | "
#         "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan> Line: {line}</cyan> | "
#         "<level>{message}</level>"
#     )

#     # Defaults
#     log_level: str = os.getenv(key="LOG_LEVEL", default="INFO")
#     base_dir: str = os.path.dirname(os.path.abspath(path=__file__))
#     log_dir: str = os.path.join(base_dir, "logs")
#     os.makedirs(log_dir, exist_ok=True)

#     logger.remove()
#     logger.add(
#         sink=sys.stderr,
#         level=log_level.upper(),
#         format=LOG_FORMAT,
#         colorize=True,
#     )
#     logger.add(
#         sink=os.path.join(log_dir, "file_{time}.log"),
#         level=log_level.upper(),
#         format=LOG_FORMAT,
#         rotation="100 KB",
#         retention=1,
#         enqueue=True,
#         backtrace=True,
#         diagnose=False,
#     )
#     # logger.info("Logger configured successfully.")
#     print("INFO | Logger configured successfully.")


# # --- Executions ---
# # Set up the logger as soon as this module is imported.
# setup_logging()
