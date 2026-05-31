from mcp.server.fastmcp import FastMCP
from news_articles import NewsRepository
from news_articles import Article

mcp = FastMCP("news_articles_mcp_server")
news_repository = NewsRepository()

@mcp.tool()
async def add_article(title: str, content: str, url: str, source: str) -> None:
    """Add a new article to the database.

    Args:
        title: The title of the article
        content: The content of the article
        url: The URL of the article
        source: The source of the article
    """
    news_repository.add(Article(title=title, content=content, url=url, source=source))

@mcp.tool()
async def update_article(id: int, title: str, content: str, url: str, source: str) -> None:
    """Update an article in the database.
    
    Args:
        id: The ID of the article
        title: The title of the article
        content: The content of the article
        url: The URL of the article
        source: The source of the article
    """
    news_repository.update(id, title=title, content=content, url=url, source=source)

if __name__ == "__main__":
    mcp.run(transport="stdio")