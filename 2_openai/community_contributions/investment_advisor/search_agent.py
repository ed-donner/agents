import os
from agents import Agent, OpenAIChatCompletionsModel, Runner
from openai import AsyncOpenAI
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

INSTRUCTIONS = (
"You are a financial data research specialist with expertise in Indian stock markets. Your task is to find the latest and \
most accurate information for the specified financial metrics of the given company. \
For each metric, provide: \
- Current value/figure \
- Previous period value for comparison (QoQ or YoY as applicable) \
- Brief context if the number needs explanation \
Search for information from reliable sources such as: \
- Company's latest quarterly/annual reports \
- BSE/NSE filings \
- Reputable financial websites (Moneycontrol, Economic Times, etc.) \
- Official company investor presentations \
Ensure all data is from the most recent reporting period available and clearly indicate the reporting date. \
If any metric is not available or unclear, state this explicitly rather than providing estimated figures."
)

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL,api_key=google_api_key)

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
search_agent = Agent(name="search_agent", instructions=INSTRUCTIONS, model=gemini_model)

