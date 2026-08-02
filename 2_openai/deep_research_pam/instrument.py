import nest_asyncio
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from langfuse import get_client

def instrument():
    nest_asyncio.apply()
    OpenAIAgentsInstrumentor().instrument()
    langfuse = get_client()

    if(langfuse.auth_check()):
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")

    return langfuse

LANGFUSE = instrument()
__all__ = ['LANGFUSE'] 