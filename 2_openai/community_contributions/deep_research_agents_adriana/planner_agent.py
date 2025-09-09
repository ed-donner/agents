from pydantic import BaseModel, Field
from agents import Agent

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')

NUMBER_SEARCHES = 3

INSTRUCTIONS = f"""You are a helpful research assistant. 
    Given a user query and 3 precisley answered clarifying questions you come up with a set of web searches
    to perform to best answer the query.
    Output {NUMBER_SEARCHES} terms to query."""


class WebSearchItem(BaseModel):
    query: str = Field(description='The search term to use for the web search')
    reasoning: str = Field(description='Your reason for why this search is important to the the users query')

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description = 'A list of web searches to perform to best answer the query')


planner_agent = Agent(
    name = 'PlannerAgent',
    instructions = INSTRUCTIONS,
    model = 'gpt-4o-mini',
    output_type = WebSearchPlan
)

planner_tool = planner_agent.as_tool(tool_name = 'plan_searches', tool_description = 'Plans the web search')