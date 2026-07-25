import os
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv()

SERP_API_KEY = os.getenv("SERPER_API_KEY")
if not SERP_API_KEY:
    raise ValueError("SERP_API_KEY required")

mcp = FastMCP("search_server")

class SearchArgs(BaseModel):
    query: str = Field(description="Search query")

@mcp.tool()
def google_search(args: SearchArgs) -> str:
    try:
        url = "https://serpapi.com/search.json"
        params = {"q": args.query, "api_key": SERP_API_KEY}

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        organic = data.get("organic_results", [])[:5]

        if not organic:
            return "No results found."

        lines = []
        for item in organic:
            lines.append(
                f"**{item.get('title')}**\n{item.get('snippet')}\n🔗 {item.get('link')}"
            )

        return "\n\n".join(lines)

    except Exception as e:
        return f"Search failed: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
