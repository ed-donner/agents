from mcp.server.fastmcp import FastMCP
from briefing_database import (
    write_article,
    read_articles,
    read_reporter,
    write_reporter,
)
import json

mcp = FastMCP("briefing_server")


@mcp.tool()
async def save_article(
    reporter: str, headline: str, summary: str, sources: str
) -> str:
    """Save a news article to the briefing database.

    Args:
        reporter: The name of the reporter filing the article
        headline: The headline of the article
        summary: A concise summary of the article (2-4 sentences)
        sources: Comma-separated list of source URLs or names
    """
    return write_article(reporter, headline, summary, sources)


@mcp.tool()
async def get_articles(reporter: str, limit: int = 5) -> str:
    """Get recent articles filed by a specific reporter.

    Args:
        reporter: The name of the reporter
        limit: Maximum number of articles to return (default 5)
    """
    articles = read_articles(reporter, limit)
    if not articles:
        return f"No articles found for {reporter}"
    return json.dumps(articles, indent=2)


@mcp.tool()
async def update_beat(reporter: str, beat: str, beat_description: str) -> str:
    """Update a reporter's beat assignment and focus description.

    Args:
        reporter: The name of the reporter
        beat: The beat name (e.g., 'Tech & AI', 'Finance')
        beat_description: Detailed description of the beat focus and reporting style
    """
    write_reporter(reporter, beat, beat_description)
    return f"Beat updated for {reporter}: {beat}"


@mcp.resource("briefings://today/{reporter}")
async def read_todays_briefing(reporter: str) -> str:
    """Get recent articles for a reporter."""
    articles = read_articles(reporter.lower(), limit=10)
    if not articles:
        return f"No articles filed recently by {reporter}"
    return json.dumps(articles, indent=2)


@mcp.resource("briefings://beat/{reporter}")
async def read_beat_resource(reporter: str) -> str:
    """Get a reporter's beat description."""
    reporter_data = read_reporter(reporter.lower())
    if not reporter_data:
        return f"No beat information found for {reporter}"
    return (
        f"Beat: {reporter_data['beat']}\n"
        f"Description: {reporter_data['beat_description']}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
