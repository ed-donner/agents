import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

load_dotenv(override=True)

MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY or not OPENROUTER_API_KEY.startswith("sk-or-v1"):
    raise ValueError("OPENROUTER_API_KEY is not set or is not a valid OpenRouter API key")

if not MODEL:
    raise ValueError("MODEL is not set")

# define the list of assistants
PRIMARY_ASSISTANT = "primary_assistant"
INPUT_GUARDRAILS_ASSISTANT = "input_guardrails_assistant"
PLANNER_ASSISTANT = "planner_assistant"
EXECUTOR_ASSISTANT = "executor_assistant"
OUTPUT_GUARDRAILS_ASSISTANT = "output_guardrails_assistant"
OUTPUT_MANAGER_ASSISTANT = "output_manager_assistant"

# Job search parameters
NUM_OF_JOBS = 5
MSG_MAX_RETRY_FAILED = "Maximum number of retries reached."

# define the llm here to avoid duplication
def get_llm() -> ChatOpenAI:
    """
    Get the LLM instance.
    Args:
        kwargs: The keyword arguments to pass to the ChatOpenAI constructor
    Returns:
        The LLM instance
    """
    return ChatOpenAI(
        model=MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL
    )
