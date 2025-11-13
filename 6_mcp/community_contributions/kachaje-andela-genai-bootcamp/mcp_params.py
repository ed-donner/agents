import os
from dotenv import load_dotenv
from market import is_paid_polygon, is_realtime_polygon

load_dotenv(override=True)

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
polygon_api_key = os.getenv("POLYGON_API_KEY")

if is_paid_polygon or is_realtime_polygon:
    market_mcp = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": polygon_api_key},
    }
else:
    market_mcp = {"command": "uv", "args": ["run", "market_server.py"]}


trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "accounts_server.py"]},
    {"command": "uv", "args": ["run", "push_server.py"]},
    market_mcp,
]

local_web_search_mcp = {"command": "uv", "args": ["run", "web_search_server.py"]}

brave_search_mcp = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": brave_env,
}


def researcher_mcp_server_params(name: str, use_local_search: bool = True):
    """Get MCP server parameters for the researcher.
    
    Args:
        name: Name identifier for the memory database
        use_local_search: If True, use local DuckDuckGo search (default). If False, use Brave search.
    
    Returns:
        List of MCP server parameter dictionaries
    """
    search_server = local_web_search_mcp if use_local_search else brave_search_mcp
    
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        search_server,
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]
