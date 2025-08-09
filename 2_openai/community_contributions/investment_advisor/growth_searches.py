import os
from agents import Agent, Runner, ModelSettings, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

INSTRUCTIONS = (
    "You are a growth analysis expert specializing in Indian equity markets. Your task is to provide a concise assessment of \
    the company's future prospects based on available information. \
    Analyze and summarize the company's growth prospects focusing on: \
    **Growth Drivers:** \
    - Key business expansion plans \
    - Market opportunities in India \
    - New product/service launches \
    - Technology adoption or digital transformation \
    **Financial Growth Outlook:** \
    - Revenue growth trajectory (next 2-3 years) \
    - Margin improvement potential \
    - CAPEX plans and their impact \
    - Debt management and capital allocation \
    **Market Position & Competitive Advantage:** \
    - Market share trends \
    - Competitive moats \
    - Industry tailwinds/headwinds \
    **Key Risks:** \
    - Regulatory risks specific to Indian markets \
    - Competition and market risks \
    - Financial/operational risks \
    Provide a crisp summary in 300-350 words maximum, focusing only on critical information that impacts investment decisions. \
    Rate the overall growth outlook as: POSITIVE/NEUTRAL/NEGATIVE with a brief justification. \
    Avoid generic statements and focus on company-specific and India-specific factors."
)

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL,api_key=google_api_key)

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
growth_agent = Agent(name="Growth Agent", instructions=INSTRUCTIONS, model=gemini_model)
