import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

_ROOT = Path(__file__).resolve().parent


def _libsql_memory_url(trader_name: str) -> str:
    mem = _ROOT / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    return (mem / f"{trader_name}.db").resolve().as_uri()

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}

# Traders: fake USD + spot crypto accounts, push, crypto market data
trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "accounts_server.py"]},
    {"command": "uv", "args": ["run", "push_server.py"]},
    {"command": "uv", "args": ["run", "crypto_market_server.py"]},
]


def researcher_mcp_server_params(name: str):
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
            "env": {"LIBSQL_URL": _libsql_memory_url(name)},
        },
    ]
