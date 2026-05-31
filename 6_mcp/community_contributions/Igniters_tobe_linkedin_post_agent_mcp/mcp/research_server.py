from mcp.server.fastmcp import FastMCP

from services.research import get_research_service


mcp = FastMCP("research_server")
service = get_research_service()


@mcp.tool()
def search_web(query: str, max_results: int = 5) -> list[dict]:
    return service.search_web(query=query, max_results=max_results)


@mcp.tool()
def fetch_page(url: str) -> dict:
    return service.fetch_page(url=url)


@mcp.tool()
def extract_article(url: str, html: str | None = None) -> dict:
    return service.extract_article(url=url, html=html)


@mcp.tool()
def collect_topic_sources(
    idea_id: str,
    topic: str,
    goal: str,
    notes: str = "",
    urls: list[str] | None = None,
) -> dict:
    return service.collect_topic_sources(
        idea_id=idea_id,
        topic=topic,
        goal=goal,
        notes=notes,
        urls=urls or [],
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
