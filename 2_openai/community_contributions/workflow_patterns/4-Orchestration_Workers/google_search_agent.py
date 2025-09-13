import os
from typing import Any

import requests
from agents import function_tool
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from schemas import SearchResult, SearchResults


def fetch_page_content(url: str) -> str:
    try:
        page: requests.Response = requests.get(url=url, timeout=10)
        # Use page.text which attempts to decode content based on HTTP headers
        soup = BeautifulSoup(markup=page.text, features="html.parser")
        text: str = soup.get_text()
        return text[:2000]  # Return first 2000 characters
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


@function_tool
def run_google_search(query: str) -> list[dict[str, str]]:
    """Run a Google search and return the results"""
    try:
        search_results = SearchResults(results=[])
        service: Any = build(
            "customsearch", "v1", developerKey=os.environ.get("GOOGLE_SEARCH_API_KEY")
        )
        res: Any = (
            service.cse()
            .list(
                q=f"{query}",
                cx=f"{os.environ.get("GOOGLE_SEARCH_CONTEXT")}",
            )
            .execute()
        )

        for item in res.get("items", []):
            content: str = fetch_page_content(item["link"])
            search_results.results.append(
                SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    content=content,
                )
            )

    except Exception as e:
        print(f"ERROR | Google Search failed: {e}")
        # search_results = SearchResults(results=[SearchResult(title="Error", link="", content=str(e))])

    return search_results
