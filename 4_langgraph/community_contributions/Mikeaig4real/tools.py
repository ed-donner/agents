"""Tools for the Job Hunter"""

import os
import re
import requests
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
from dotenv import load_dotenv

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()


async def playwright_tools():
    """Launch headless browser and return Playwright tools, browser, and playwright instance."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def convert_gdoc_url(url: str) -> str:
    """Convert a Google Docs URL to its plain text export URL."""
    match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    if match:
        doc_id = match.group(1)
        return f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    return url



def search_jobs(query: str) -> str:
    """Search for active job postings and return structured results with links."""
    results = serper.results(f"{query} job openings apply deadline 2026")
    organic = results.get("organic", [])
    
    output = []
    for item in organic[:5]:
        title = item.get("title", "No Title")
        link = item.get("link", "No Link")
        snippet = item.get("snippet", "No Snippet")
        output.append(f"Title: {title}\nURL: {link}\nSnippet: {snippet}\n---")
    
    if not output:
        return "No job results found."
        
    return "\n".join(output)


def push(text: str) -> str:
    """Send a push notification to the user via Pushover."""
    requests.post(
        pushover_url,
        data={"token": pushover_token, "user": pushover_user, "message": text}
    )
    return "success"


async def other_tools():
    """Return non-browser tools: search, push notification."""
    tool_search = Tool(
        name="search_jobs",
        func=search_jobs,
        description="Search the web for active job postings matching given skills or keywords"
    )

    tool_push = Tool(
        name="send_push_notification",
        func=push,
        description=(
            "Use this tool when you want to send a push notification to the user"
        )
    )

    return [tool_search, tool_push]
