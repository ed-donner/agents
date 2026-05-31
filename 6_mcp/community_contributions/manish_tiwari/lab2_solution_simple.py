"""
Lab 2 — Simple exercise: MCP server that exposes "today's date" as a tool.

What this is
------------
- An MCP *server* is a small program that speaks the MCP protocol over stdio.
- Tools are just Python functions you register with @mcp.tool().
- An AI agent (or a custom client) connects to this process and can call those tools.

How to run the server (from the 6_mcp folder, same as accounts_server.py in the lab)
------------------------------------------------------------------------------------
    cd 6_mcp
    uv run community_contributions/manish_tiwari/lab2_solution_simple.py

How to use it with the OpenAI Agents SDK (like 2_lab2.ipynb)
-------------------------------------------------------------
    from agents.mcp import MCPServerStdio

    params = {
        "command": "uv",
        "args": ["run", "community_contributions/manish_tiwari/lab2_solution_simple.py"],
    }
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        tools = await server.list_tools()
        # ... build Agent(..., mcp_servers=[server]) and ask "What is today's date?"
"""

from datetime import date

from mcp.server.fastmcp import FastMCP
# Name shown to MCP clients (helps when you have several servers).
mcp = FastMCP("datetime_server")


@mcp.tool()
async def get_today_date() -> str:
    """Return today's calendar date in ISO format (YYYY-MM-DD).

    Use this when the user asks for today's date, the current date, or what day it is.
    """
    return date.today().isoformat()


if __name__ == "__main__":
    # stdio = the lab default: the parent process (uv / IDE / client) talks over pipes.
    mcp.run(transport="stdio")
