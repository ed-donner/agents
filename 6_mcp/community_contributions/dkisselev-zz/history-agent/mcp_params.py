import os
from pathlib import Path
from dotenv import load_dotenv
from market import is_paid_polygon, is_realtime_polygon

load_dotenv(override=True)

# Get absolute path to script directory
SCRIPT_DIR = Path(__file__).parent.absolute()

# Ensure required directories exist
(SCRIPT_DIR / "memory").mkdir(exist_ok=True)
(SCRIPT_DIR / "sandbox").mkdir(exist_ok=True)

# Environment variables for npm to suppress non-JSON output to STDOUT
NPM_SILENT_ENV = {
    "NPM_CONFIG_LOGLEVEL": "error",  # Only show errors, not info messages
    "NPM_CONFIG_UPDATE_NOTIFIER": "false",  # Disable update notifications
    "NPM_CONFIG_FUND": "false",  # Disable funding messages
    "NPM_CONFIG_AUDIT": "false",  # Disable audit messages
}

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY"), **NPM_SILENT_ENV}
polygon_api_key = os.getenv("MASSIVE_API_KEY")


# The MCP server for the Trader to read Market Data

if is_paid_polygon or is_realtime_polygon:
    market_mcp = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/massive-com/mcp_massive@v0.1.0", "mcp_massive"],
        "env": {"MASSIVE_API_KEY": polygon_api_key},
    }
else:
    market_mcp = {"command": "uv", "args": ["run", str(SCRIPT_DIR / "market_server.py")]}


print(f"DEBUG: MASSIVE_API_KEY loaded: {polygon_api_key is not None}")
print(f"DEBUG: is_paid_polygon: {is_paid_polygon}, is_realtime_polygon: {is_realtime_polygon}")
print(f"DEBUG: market_mcp config: {market_mcp}")


# The full set of MCP servers for the trader: Accounts, Push Notification and the Market

trader_mcp_server_params = [
    {"command": "uv", "args": ["run", str(SCRIPT_DIR / "accounts_server.py")]},
    {"command": "uv", "args": ["run", str(SCRIPT_DIR / "push_server.py")]},
    market_mcp,
]

# The full set of MCP servers for the researcher: Fetch, Brave Search and Memory


def researcher_mcp_server_params(name: str):
    memory_dir = SCRIPT_DIR / "memory"
    memory_dir.mkdir(exist_ok=True)
    
    # Environment for memory server with npm silencing
    memory_env = {
        "LIBSQL_URL": f"file:{memory_dir}/{name}.db",
        **NPM_SILENT_ENV
    }
    
    return [
        # {"command": "uvx", "args": ["mcp-server-fetch"]},  # Disabled - ESM error
        {
            "command": "npx",
            "args": ["--quiet", "-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        },
        {
            "command": "npx",
            "args": ["--quiet", "-y", "mcp-memory-libsql"],
            "env": memory_env,
        },
    ]
