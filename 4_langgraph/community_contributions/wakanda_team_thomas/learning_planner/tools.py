"""
Tool definitions for the Learning Path Generator.
"""

from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv(override=True)


def get_wikipedia_tool():
    """Create and return the Wikipedia search tool."""
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    return wiki_tool


def get_search_tool():
    """Create and return the Tavily web search tool."""
    search_tool = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
    )
    return search_tool
