import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)


LLM_PROVIDERS = {
    # api_key, base_url, model
    'ollama_cloud': (os.getenv('OLLAMA_API_KEY'), 'https://ollama.com/v1', 'gpt-oss:120b'),
    'cerebras': (os.getenv('CEREBRAS_API_KEY'), 'https://api.cerebras.ai/v1', 'gpt-oss-120b'),
}
LLM_PROVIDER = 'cerebras'

api_key, base_url, model = LLM_PROVIDERS[LLM_PROVIDER]

memory = MemorySaver()

llm = init_chat_model(
    model=model,
    model_provider='openai',
    api_key=api_key,
    base_url=base_url,
)
