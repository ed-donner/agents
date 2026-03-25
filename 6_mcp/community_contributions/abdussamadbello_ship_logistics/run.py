"""
Run the ship logistics MCP server over stdio (for Cursor / Claude / MCP clients).
"""

from server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
