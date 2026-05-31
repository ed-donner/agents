from mcp.server.fastmcp import FastMCP
import dockertool
import searchtool
import msg_agent
from typing import List, Dict

mcp = FastMCP("my_mcp_server")

@mcp.tool()
async def run_docker() -> str:
    """Run Docker container and return response.
    """
    return dockertool.run_docker()


@mcp.tool()
async def web_search(query: str, safe_search: str = "moderate") -> List[Dict[str, str]]:
    """Search the web with DuckDuckGo and return up the results.

    Args:
        query: The query term to search the internet for
        safe_search: "off" | "moderate" | "strict"
    """
    return searchtool.web_search(query, safe_search)


@mcp.tool()
async def send_msg(query: str, concise_report: str) -> str:
    """Send a message to telegram using the original query and concise report

    Args:
        query: The query given by the user
        concise_report: The generated report
    """
    return msg_agent.send_msg(query, concise_report)


if __name__ == "__main__":
    mcp.run(transport='stdio')
