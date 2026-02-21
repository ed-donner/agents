""" Web Search Agent
This agent is responsible for generating a set of web search queries to perform to best answer the query.
"""

from agents import Agent
from pydantic import BaseModel, Field

HOW_MANY_SEARCHES = 3
search_instructions = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

class WebSearchQueryItem(BaseModel):
    reason: str = Field(description="Provide reasoning why this specific web search query item is needed")
    query: str = Field(description="The search term to use for the web search")

class WebSearches(BaseModel):
    web_search_queries: list[WebSearchQueryItem] = Field(description = "List of web search queries as WebSearchQueryItem objects")

class WebSearchAgent:
    def __init__(self):
        self.web_search_query_agent = None

    def get_web_agent(self):
        return self.web_search_query_agent
    
    def create_web_agent(self):
        self.web_search_query_agent = Agent(
            name="SearchAgent",
            instructions=search_instructions,
            model="gpt-4o-mini",
            output_type=WebSearches
        )