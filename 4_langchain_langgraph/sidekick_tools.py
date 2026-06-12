"""Tools for the Sidekick: a mix of MCP servers, ready-made LangChain tools and our own."""

import os

import requests
import wikipedia
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

# Wikimedia rejects the wikipedia library's default user agent, so identify ourselves properly
wikipedia.set_user_agent("agentic-track-course (https://edwarddonner.com)")


@tool
def search(query: str) -> str:
    """Search the web for current information and return the top results."""
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": os.getenv("SERPER_API_KEY"), "Content-Type": "application/json"},
        json={"q": query},
    )
    data = response.json()
    parts = []
    if "answerBox" in data:
        box = data["answerBox"]
        parts.append(box.get("answer") or box.get("snippet") or "")
    for item in data.get("organic", [])[:5]:
        parts.append(f"{item.get('title')}: {item.get('snippet')}")
    return "\n".join(p for p in parts if p)


@tool
def send_push_notification(text: str) -> str:
    """Send a short push notification to the user's phone."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={"token": os.getenv("PUSHOVER_TOKEN"), "user": os.getenv("PUSHOVER_USER"), "message": text},
    )
    return "Notification sent"


wikipedia_lookup = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())


def mcp_connections(sandbox: str, config_path: str) -> dict:
    """The MCP servers the Sidekick uses: a headful browser and a sandbox filesystem."""
    return {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--config", config_path, "--isolated"],
            "env": {"PLAYWRIGHT_MCP_HEADLESS": "false"},
        },
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox],
        },
    }


async def get_all_tools(sandbox: str, config_path: str):
    """Return the full tool list (our tools plus the MCP server tools) and the MCP client."""
    client = MultiServerMCPClient(mcp_connections(sandbox, config_path))
    mcp_tools = await client.get_tools()
    our_tools = [search, send_push_notification, wikipedia_lookup]
    return our_tools + mcp_tools, client
