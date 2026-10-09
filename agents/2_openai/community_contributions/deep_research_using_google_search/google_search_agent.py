import os
from pprint import pprint
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
from agents import function_tool
from googleapiclient.discovery import build
from pydantic import BaseModel, Field

load_dotenv(override=True)
api_key=os.environ.get('GOOGLE_SEARCH_API_KEY')
search_context=os.environ.get('GOOGLE_SEARCH_CONTEXT')

class SearchResult(BaseModel):
    title: str = Field(description="The title of the search result.")
    link: str = Field(description="The URL of the search result.")
    content: str = Field(description="The content snippet of the search result.")

class SearchResults(BaseModel):
    results: list[SearchResult] = Field(description="A list of search results.")

def fetch_page_content(url):
    try:
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        text = soup.get_text()
        return text[:2000]  # Return first 1000 characters
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


@function_tool
def run_google_search(query:str) -> list[dict[str, str]]:
    """ Run a Google search and return the results """
    search_results = SearchResults(results=[])
    service = build("customsearch", "v1", developerKey=api_key)
    res = (
        service.cse()
        .list(
            q=f'{query}',
            cx=f'{search_context}',
        )
        .execute()
    )

    for item in res.get('items', []):
        content = fetch_page_content(item['link'])
        search_results.results.append(SearchResult(
            title=item.get('title', ''),
            link=item.get('link', ''),
            content=content
        ))
    return search_results
