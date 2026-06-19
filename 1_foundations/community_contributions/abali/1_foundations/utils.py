import os
from dotenv import load_dotenv
import os
import json
import requests 
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
# api keys 
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set (and this is optional)")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:2]}")
else:
    print("Google API Key not set (and this is optional)")

if deepseek_api_key:
    print(f"DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
else:
    print("DeepSeek API Key not set (and this is optional)")

if groq_api_key:
    print(f"Groq API Key exists and begins {groq_api_key[:4]}")
else:
    print("Groq API Key not set (and this is optional)")

# load the api keys 
load_dotenv(override=True)

# instantiate LLM clients 
openai = OpenAI()
anthropic = Anthropic()
ollama = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
deepseek = OpenAI(base_url='https://api.deepseek.com/v1', api_key=deepseek_api_key)

# Functions 
def ask_openai(messages:str, model_name):
    """
    Ask the OpenAI API with the given messages and model name.
    If model_name is None, use the default model "gpt-4o-mini".
    Returns the response content.
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini" if model_name is None else model_name,
        messages=messages,
    )
    return response.choices[0].message.content

def ask_anthropic(messages:str, model_name):
    """
    Ask the Anthropic API with the given messages and model name.
    If model_name is None, use the default model "claude-3-5-sonnet-20240620".
    Returns the response content.
    """
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20240620" if model_name is None else model_name,
        messages=messages,
        max_tokens=1000
    )
    return response.content[0].text

def ask_ollama(messages:str, model_name):
    """
    Ask the Ollama API with the given messages and model name.
    If model_name is None, use the default model "llama3.2".
    Returns the response content.
    """
    response = ollama.chat.completions.create(
        model="llama3.2" if model_name is None else model_name,
        messages=messages,
    )
    return response.choices[0].message.content

def ask_deepseek(messages:str, model_name):
    """
    Ask the DeepSeek API with the given messages and model name.
    If model_name is None, use the default model "deepseek-chat".
    Returns the response content.
    """
    response = deepseek.chat.completions.create(
        model="deepseek-chat" if model_name is None else model_name,
        messages=messages,
    )
    return response.choices[0].message.content

# define the mapping of LLM names to functions
lmm_func_map = {
    "openai": ask_openai,
    "anthropic": ask_anthropic,
    "ollama": ask_ollama,
    "deepseek": ask_deepseek
}

def ask_llm(llm:str, messages:str, model_name=None):
    """
    Ask the LLM with the given messages and model name.
    If model_name is None, use the default model for the LLM.
    Returns the response content.
    """

    try:
        return lmm_func_map[llm](messages, model_name)
    except KeyError:
        raise ValueError(f"LLM {llm} not supported")