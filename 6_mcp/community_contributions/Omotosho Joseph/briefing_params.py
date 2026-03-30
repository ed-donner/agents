import os
from dotenv import load_dotenv

load_dotenv(override=True)

serper_env = {"SERPER_API_KEY": os.getenv("SERPER_API_KEY")}

briefing_mcp_server_params = [
    {"command": "uv", "args": ["run", "briefing_server.py"]},
]


def researcher_mcp_server_params(name: str):
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "serper-search-scrape-mcp-server"],
            "env": serper_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]
