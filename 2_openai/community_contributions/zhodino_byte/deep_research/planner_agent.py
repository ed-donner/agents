from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")
HOW_MANY_SEARCHES = int(os.getenv("HOW_MANY_SEARCHES", 5))

BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "openai/gpt-4o-mini")

openrouter_client = AsyncOpenAI(base_url=BASE_URL, api_key=OPENROUTER_API_KEY)
model = OpenAIChatCompletionsModel(openai_client=openrouter_client, model=MODEL_NAME)


INSTRUCTIONS = f"""
You are a research assistant. Given a user query and clarifying questions, come up with a set of web searches
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for.
"""


class WebSearchItem(BaseModel):
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


planner_agent = Agent(
    name="Planner Agent",
    instructions=INSTRUCTIONS,
    model=model,
    output_type=WebSearchPlan,
)
