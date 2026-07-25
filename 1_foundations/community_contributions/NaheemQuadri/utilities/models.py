from pydantic import BaseModel
from openai import OpenAI
from typing import Literal

from utilities.settings import Settings



class Model:
 
    def __init__(self, type: str):
        self.type = type
        self.settings = Settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.openrouter_client = OpenAI(api_key=self.settings.openrouter_api_key, base_url=self.settings.openrouter_base_url)
        self.ollama_client = OpenAI(base_url=self.settings.ollama_base_url, api_key="ollama")
        self.huggingface_client = OpenAI(api_key=self.settings.hf_token,base_url=self.settings.hf_base_url)
        

    def get_model(self, model_name: str, messages, tools=[], tool_choice: Literal["none", "auto", "required"]="auto"):
        
        if self.type == "openai":
            reply = self.openai_client.chat.completions.create(model=model_name, messages=messages, tools=tools, tool_choice=tool_choice)
            print(reply.usage)
        elif self.type == "openrouter":
            reply = self.openrouter_client.chat.completions.create(model=model_name, messages=messages, tools=tools, tool_choice=tool_choice)
            print(reply.usage)
        elif self.type == "ollama":
            reply = self.ollama_client.chat.completions.create(model=model_name, messages=messages, tools=tools, tool_choice=tool_choice)
            print(reply.usage)
        elif self.type == "huggingface":
            reply = self.huggingface_client.chat.completions.create(model=model_name, messages=messages, tools=tools, tool_choice=tool_choice)
        else:
            raise ValueError(f"Invalid model type: {self.type}")

        return reply