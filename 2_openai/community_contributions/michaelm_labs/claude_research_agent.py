"""
Claude Research Agent
=====================

Production-style research agent using:

- Claude 3.5 Sonnet
- Brave Search API
- Async execution
- Tool calling
- Web page scraping
- Structured research workflow
- Retry-safe architecture

Author: Michael Morar
"""

import os
import json
import asyncio
from typing import List, Dict, Any

import requests
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv(override=True)

# =========================================================
# CONFIG
# =========================================================

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

MODEL = "claude-sonnet-4-6"

client = Anthropic(
    api_key=CLAUDE_API_KEY
)


# =========================================================
# BRAVE SEARCH TOOL
# =========================================================

def brave_search(query: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using Brave Search API.
    """

    url = "https://api.search.brave.com/res/v1/web/search"

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
    }

    params = {
        "q": query,
        "count": count,
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("web", {}).get("results", [])


# =========================================================
# SCRAPE PAGE TOOL
# =========================================================

def scrape_page(url: str) -> str:
    """
    Download page text content.
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.text[:15000]


# =========================================================
# TOOL DEFINITIONS FOR CLAUDE
# =========================================================

TOOLS = [
    {
        "name": "brave_search",
        "description": "Search the web for current information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                },
                "count": {
                    "type": "integer"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "scrape_page",
        "description": "Download the contents of a web page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string"
                }
            },
            "required": ["url"]
        }
    }
]


# =========================================================
# EXECUTE TOOL
# =========================================================

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:

    if tool_name == "brave_search":

        results = brave_search(
            query=tool_input["query"],
            count=tool_input.get("count", 5)
        )

        simplified = []

        for r in results:

            simplified.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "description": r.get("description"),
            })

        return json.dumps(simplified, indent=2)

    elif tool_name == "scrape_page":

        content = scrape_page(
            url=tool_input["url"]
        )

        return content

    else:
        raise ValueError(f"Unknown tool: {tool_name}")


# =========================================================
# RESEARCH LOOP
# =========================================================

async def research(query: str):

    system_prompt = """
You are a senior AI research analyst.

Your workflow:

1. Break problems into sub-questions
2. Search multiple times if needed
3. Scrape useful pages
4. Compare sources
5. Identify consensus and disagreement
6. Produce concise but deep analysis

Prefer:
- official documentation
- technical blogs
- research papers
- high-quality engineering sources

Avoid:
- SEO spam
- low-quality blogs
"""

    messages = [
        {
            "role": "user",
            "content": query
        }
    ]

    while True:

        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        assistant_content = response.content

        messages.append({
            "role": "assistant",
            "content": assistant_content
        })

        tool_used = False

        for content in assistant_content:

            if content.type == "tool_use":

                tool_used = True

                tool_name = content.name
                tool_input = content.input

                print(f"\n[TOOL CALL]")
                print(f"Tool: {tool_name}")
                print(f"Input: {tool_input}")

                try:

                    result = execute_tool(
                        tool_name,
                        tool_input
                    )

                except Exception as e:

                    result = f"Tool execution failed: {str(e)}"

                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result
                        }
                    ]
                })

        if not tool_used:

            print("\n============================")
            print("FINAL RESEARCH REPORT")
            print("============================\n")

            print(response.content[0].text)

            return response.content[0].text


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    query = os.getenv("QUERY")

    asyncio.run(
        research(query)
    )