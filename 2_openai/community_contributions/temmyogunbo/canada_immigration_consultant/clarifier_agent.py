import base64
import json
from agents import Agent,Runner, trace

from typing import Dict, Any
from PIL import Image
import pytesseract
import cv2
from openai import OpenAI
from pydantic import BaseModel, Field


OLLAMA_BASE_URL = "http://localhost:11434/v1"

ollama = OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
class ClarifyingQuestion(BaseModel):
    is_canada_based: bool = Field(description="Whether the question is about Canada or Canadian immigration")

INSTRUCTIONS = """
You are a helpful assistant on Canadian Immigration. You are given a query and understand the user's true intent.
Determine if the question is about Canada or Canadian immigration. If the question pertains to another country or is not Canada-related, set is_canada_based to False.
"""



def Clarify_query(query: str) -> ClarifyingQuestion:
    """ Clarify the query """
    messages = [
        {"role": "system", "content": INSTRUCTIONS + "\n\nRespond with ONLY valid JSON in this format: {\"is_canada_based\": true} or {\"is_canada_based\": false}"},
        {"role": "user", "content": query},
    ]
    response = client.chat.completions.create(model="llama3", messages=messages)
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return ClarifyingQuestion(**{k: v for k, v in data.items() if k in ClarifyingQuestion.model_fields})
    except (json.JSONDecodeError, TypeError):
        return ClarifyingQuestion(is_canada_based=True)  # Default to allowing when parsing fails