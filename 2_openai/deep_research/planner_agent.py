from pydantic import BaseModel, Field
from agents import Agent,  OpenAIChatCompletionsModel
from openai import AsyncOpenAI
import os

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

google_api_key = os.getenv('GOOGLE_API_KEY')
if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:2]}")
else:
    print("Google API Key not set (and this is optional)")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-pro", openai_client=gemini_client)


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=WebSearchPlan,
)