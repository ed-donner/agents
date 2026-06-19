"""
@Author: John T
@LinkedIn: www.linkedin.com/in/john-tavolacci
@Github: https://github.com/johnbikes/
@Date: 2025-06-07
@Description: A basic MCP server for comparing faces from two URLs using InsightFace.
@License: Apache License 2.0
"""

from mcp.server.fastmcp import FastMCP
from same_from_urls import is_same

mcp = FastMCP("insight_server")

@mcp.tool()
async def get_is_same(url1: str, url2: str) -> bool:
    """Compare two URLs to determine if they containW the same face according to insightface.
    
    Args:
        url1 (str): First URL to compare
        url2 (str): Second URL to compare
        
    Returns:
        bool: True if the URLs point to the same face according to insightface, False otherwise or if no face found
    """
    return is_same(url1, url2)

# TODO: possible embeddings store
# @mcp.resource

if __name__ == "__main__":
    mcp.run(transport='stdio')