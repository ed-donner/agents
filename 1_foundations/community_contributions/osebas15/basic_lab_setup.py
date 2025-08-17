"""
Basic lab setup module for easy initialization of LLM clients across labs.
Handles API key checking and client creation for various providers.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from IPython.display import Markdown, display

# Global client objects
openai_client = None
anthropic_client = None
ollama_client = None
google_client = None
deepseek_client = None
groq_client = None

# Default models for each provider
DEFAULT_MODELS = {
    'openai': 'gpt-4o-mini',
    'anthropic': 'claude-3-5-sonnet-20241022',
    'ollama': 'llama3.2',
    'google': 'gemini-2.0-flash-exp',
    'deepseek': 'deepseek-chat',
    'groq': 'llama-3.3-70b-versatile'
}

def setup():
    """
    Initialize the lab setup by loading environment variables and creating client objects.
    Uses load_dotenv(override=True) for safe handling of API keys.
    """
    global openai_client, anthropic_client, ollama_client, google_client, deepseek_client, groq_client
    
    # Load environment variables safely
    load_dotenv(override=True)
    
    # Check and create OpenAI client
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        print(f"✓ OpenAI client initialized (key starts with {openai_api_key[:8]}...)")
    else:
        print("⚠ OpenAI API Key not set")
    
    # Check and create Anthropic client
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_api_key:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        print(f"✓ Anthropic client initialized (key starts with {anthropic_api_key[:7]}...)")
    else:
        print("⚠ Anthropic API Key not set (optional)")
    
    # Create Ollama client (local, no API key needed)
    ollama_client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
    print("✓ Ollama client initialized (localhost)")
    
    # Check and create Google client
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        google_client = OpenAI(
            api_key=google_api_key, 
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        print(f"✓ Google client initialized (key starts with {google_api_key[:2]}...)")
    else:
        print("⚠ Google API Key not set (optional)")
    
    # Check and create DeepSeek client
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_api_key:
        deepseek_client = OpenAI(
            api_key=deepseek_api_key, 
            base_url="https://api.deepseek.com/v1"
        )
        print(f"✓ DeepSeek client initialized (key starts with {deepseek_api_key[:3]}...)")
    else:
        print("⚠ DeepSeek API Key not set (optional)")
    
    # Check and create Groq client
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        groq_client = OpenAI(
            api_key=groq_api_key, 
            base_url="https://api.groq.com/openai/v1"
        )
        print(f"✓ Groq client initialized (key starts with {groq_api_key[:4]}...)")
    else:
        print("⚠ Groq API Key not set (optional)")
    
    print("\nSetup complete! Available clients:")
    available_clients = []
    if openai_client:
        available_clients.append("OpenAI")
    if anthropic_client:
        available_clients.append("Anthropic")
    if ollama_client:
        available_clients.append("Ollama")
    if google_client:
        available_clients.append("Google")
    if deepseek_client:
        available_clients.append("DeepSeek")
    if groq_client:
        available_clients.append("Groq")
    
    print(f"  {', '.join(available_clients)}")

def get_available_clients():
    """
    Return a dictionary of available clients and their default models.
    """
    clients = {}
    if openai_client:
        clients['openai'] = {'client': openai_client, 'model': DEFAULT_MODELS['openai']}
    if anthropic_client:
        clients['anthropic'] = {'client': anthropic_client, 'model': DEFAULT_MODELS['anthropic']}
    if ollama_client:
        clients['ollama'] = {'client': ollama_client, 'model': DEFAULT_MODELS['ollama']}
    if google_client:
        clients['google'] = {'client': google_client, 'model': DEFAULT_MODELS['google']}
    if deepseek_client:
        clients['deepseek'] = {'client': deepseek_client, 'model': DEFAULT_MODELS['deepseek']}
    if groq_client:
        clients['groq'] = {'client': groq_client, 'model': DEFAULT_MODELS['groq']}
    
    return clients

def get_client(provider):
    """
    Get a specific client by provider name.
    
    Args:
        provider (str): Provider name ('openai', 'anthropic', 'ollama', 'google', 'deepseek', 'groq')
    
    Returns:
        Client object or None if not available
    """
    clients = get_available_clients()
    return clients.get(provider, {}).get('client')

def get_default_model(provider):
    """
    Get the default model for a specific provider.
    
    Args:
        provider (str): Provider name
    
    Returns:
        str: Default model name or None if provider not available
    """
    clients = get_available_clients()
    return clients.get(provider, {}).get('model')

# Convenience functions for common operations
def create_completion(provider, messages, model=None, **kwargs):
    """
    Create a completion using the specified provider.
    
    Args:
        provider (str): Provider name
        messages (list): List of message dictionaries
        model (str, optional): Model name (uses default if not specified)
        **kwargs: Additional arguments to pass to the completion call
    
    Returns:
        Completion response or None if provider not available
    """
    client = get_client(provider)
    if not client:
        print(f"Provider '{provider}' not available")
        return None
    
    if not model:
        model = get_default_model(provider)
    
    try:
        if provider == 'anthropic':
            # Anthropic has a different API structure
            response = client.messages.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 1000),
                **kwargs
            )
            return response.content[0].text
        else:
            # OpenAI-compatible APIs
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Error with {provider}: {e}")
        return None 