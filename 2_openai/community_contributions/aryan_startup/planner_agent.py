import os
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"You are a planner agent in a startup due diligence pipeline. Given a startup idea, come up with a set of web searches \
to perform to research the market, competitors, and product viability. Output {HOW_MANY_SEARCHES} search terms."


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is relevant to the due diligence.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform for startup due diligence.")


gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash-lite",
    openai_client=AsyncOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ.get("GEMINI_API_KEY"),
    ),
)
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=WebSearchPlan,
)