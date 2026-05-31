import os, httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("serper")
KEY = os.getenv("SERPER_API_KEY", "")

async def _call(endpoint, q, n=10):
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"https://google.serper.dev/{endpoint}",
            headers={"X-API-KEY": KEY, "Content-Type": "application/json"},
            json={"q": q, "num": n}, timeout=30,
        )
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def google_search(query: str, num_results: int = 10) -> str:
    """Google search via Serper. Returns organic results."""
    data = await _call("search", query, num_results)
    out = []
    if kg := data.get("knowledgeGraph"):
        out.append(f"**{kg.get('title', '')}** -- {kg.get('description', '')}")
    for hit in data.get("organic", []):
        out.append(f"**{hit['title']}**\n{hit['link']}\n{hit.get('snippet', '')}")
    return "\n\n---\n\n".join(out) or "No results."

@mcp.tool()
async def google_news(query: str, num_results: int = 10) -> str:
    """Google News via Serper. Returns recent articles."""
    data = await _call("news", query, num_results)
    out = []
    for hit in data.get("news", []):
        out.append(f"**{hit['title']}** ({hit.get('date', '?')})\n{hit['link']}\n{hit.get('snippet', '')}")
    return "\n\n---\n\n".join(out) or "No news."

if __name__ == "__main__":
    mcp.run(transport="stdio")
