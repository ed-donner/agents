from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel, Runner
from openai import AsyncOpenAI
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv(override=True)

metrics = 5

INSTRUCTIONS = (
"You are a financial planning expert specializing in the Indian stock market. Your task is to identify the top {metrics} most critical \
financial metrics to evaluate for the given company. Consider: \
- Industry-specific metrics that matter most for this sector \
- Standard financial health indicators \
- Valuation metrics appropriate for Indian markets \
- Growth and profitability measures \
- Risk assessment metrics \
Focus on metrics that will provide the most comprehensive view of the company's financial health, growth potential, and \
investment attractiveness in the Indian market context."
)


class WebSearchItem(BaseModel):
    query: str = Field(description="Just name of the metric use for search.")
    company_name: str = Field(description="The company name provided by user.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL,api_key=google_api_key)

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
planner_agent = Agent(name="PlannerAgent", instructions=INSTRUCTIONS, model=gemini_model, output_type=WebSearchPlan)