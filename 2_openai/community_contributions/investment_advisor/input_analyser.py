from sys import flags
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from openai import OpenAI
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv(override=True)


INSTRUCTIONS = f"You are an intelligent and experienced financial analyst. For provided input you first check if \
it's valid listed company in India stock market or not. Only if it's listed in India, you need to pass the correct company name and true in output. \
If company name provided in input is not valid listed company in India or if there is no company name, output false and according to input share \
the output in humourous sarcastic tone conveying you can not assist with this information \
that this is out of scope and you can only share information about listed companies in India. You always have to be empathetic."

class InputValidation(BaseModel):
    valid: bool = Field(description="Just TRUE or FALSE according to input validation check")
    company_name: str = Field(description="The company name provided by user or humourous output.")


google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL,api_key=google_api_key)

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
input_analyser = Agent(name="Input Analyser", instructions=INSTRUCTIONS, model=gemini_model, output_type= InputValidation)