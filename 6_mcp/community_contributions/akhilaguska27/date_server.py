# =============================================================================
# DATE MCP SERVER
# by akhilaguska27
# =============================================================================
# WHAT IS THIS?
# This is a custom MCP (Model Context Protocol) server that exposes date and
# time tools so that any AI agent can call them to get the current date/time.
#
# WHY BUILD THIS?
# Agents don't know the current date/time unless we tell them.
# Instead of hardcoding the date in the system prompt, we expose it as a tool
# so the agent can call it whenever it needs — always getting the real time.
#
# HOW DOES IT WORK?
# 1. We use FastMCP to create an MCP server (same pattern as accounts_server.py)
# 2. We decorate functions with @mcp.tool() to expose them as MCP tools
# 3. When an agent needs the date, it calls our tool via the MCP protocol
# 4. The server runs as a subprocess and communicates via stdio traport
#
# HOW TO USE THIS?
# params = {"command": "uv", "args": ["run", "date_server.py"]}
# async with MCPServerStdio(params=params) as mcp_server:
#     agent = Agent(..., mcp_servers=[mcp_server])
# =============================================================================

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import pytz

# Create the MCP server instance — give it a name
mcp = FastMCP("date_server")


# -----------------------------------------------------------------------------
# TOOL 1: Get current date and time in UTC
# The simplest tool — returns current UTC datetime as a string
# -----------------------------------------------------------------------------
@mcp.tool()
async def get_current_date() -> str:
    """Get the current date and time in UTC.
    Returns the current date and time as a formatted string.
    """
    return datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# --------------------------------------------------------------------------# TOOL 2: Get date/time in a specific timezone
# Useful when the agent or user is in a specific part of the world
# Examples: "America/Chicago", "Asia/Kolkata", "Europe/London"
# -----------------------------------------------------------------------------
@mcp.tool()
async def get_date_in_timezone(timezone: str) -> str:
    """Get the current date and time in a specific timezone.
    Args:
        timezone: The timezone name (e.g. 'America/Chicago', 'Asia/Kolkata', 'Europe/London')
    """
    try:
        tz = pytz.timezone(timezone)
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Unknown timezone: {timezone}. Example valid timezones: America/Chicago, Asia/Kolkata, Europe/London"


# -----------------------------------------------------------------------------
# TOOL 3: Get the current day of the week
# Simple helper — returns "Monday", "Tuesday" etc.
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_day_of_week() -> str:
    """Get the current day of the week."""
    return datetime.now().strftime("%A")


# -----------------------------------------------------------------------------
# ENTRY POINT
# Run the server using stdio transport (communicates via stdin/stdout)
# This is how MCPServerStdio spawns and talks to this server
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport='stdio')
