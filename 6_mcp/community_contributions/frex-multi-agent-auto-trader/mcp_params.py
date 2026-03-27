import os
from dotenv import load_dotenv

load_dotenv(override=True)

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN", "free")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"

# Directory this file lives in — used to run local MCP servers from any cwd
HERE = os.path.dirname(os.path.abspath(__file__))

print(f"[mcp_params] HERE={HERE}, polygon_plan={polygon_plan}")

# Market MCP (tiered by Polygon plan) 

if is_paid_polygon or is_realtime_polygon:
    market_mcp = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": polygon_api_key},
    }
else:
    market_mcp = {
        "command": "uv",
        "args": ["run", "--directory", HERE, "market_server.py"],
    }

# Execution Trader MCP servers 

trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "--directory", HERE, "accounts_server.py"]},
    {"command": "uv", "args": ["run", "--directory", HERE, "push_server.py"]},
    {"command": "uv", "args": ["run", "--directory", HERE, "risk_server.py"]},
    market_mcp,
]

# Risk Manager Agent MCP servers ─

risk_manager_mcp_server_params = [
    {"command": "uv", "args": ["run", "--directory", HERE, "risk_server.py"]},
]

# Researcher MCP servers 

def researcher_mcp_server_params(name: str):
    memory_dir = os.path.join(HERE, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:{memory_dir}/{name}.db"},
        },
    ]
