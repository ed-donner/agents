from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

# All stdio MCP Python servers for this contribution live in this folder (copies of the 6_mcp lab
# files where needed). Use absolute paths + cwd so `uv run` works from any directory.
_CONTRIB_DIR = Path(__file__).resolve().parent
_CWD = str(_CONTRIB_DIR)

trader_mcp_server_params = [
    {"command": "uv", "args": ["run", str(_CONTRIB_DIR / "accounts_server.py")], "cwd": _CWD},
    {"command": "uv", "args": ["run", str(_CONTRIB_DIR / "push_server.py")], "cwd": _CWD},
    {"command": "uv", "args": ["run", str(_CONTRIB_DIR / "market_server.py")], "cwd": _CWD},
]


def researcher_mcp_server_params(name: str):
    return [
        {"command": "uv", "args": ["run", str(_CONTRIB_DIR / "ddg_search_server.py")], "cwd": _CWD},
        {"command": "uvx", "args": ["mcp-server-fetch"], "cwd": _CWD},
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
            "cwd": _CWD,
        },
    ]
