from mcp.server.fastmcp import FastMCP
import datetime

mcp = FastMCP('news_server')

# @mcp.tool()
# async def get_news(topic: str, max_results: int = 5) -> str:
#     """Get the News for a given topic.
    
#     Args:
#         topic: Topic to fetch news for
        
#     Returns:
#         JSON string with: topic, fetched_at, results[{title, url}]
#     """
#     return f"Here is the news for {topic}"

@mcp.tool()
def get_current_date() -> str:
    """Get the current date
    
    """
    return f"Here is the current date:{datetime.datetime.now().strftime('%Y-%m-%d')}"


if __name__ == "__main__":
    mcp.run(transport='stdio')