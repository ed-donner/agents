"""MCP stdio params for the wellness coach + psychoeducation librarian."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def coach_mcp_server_params(user_id: str) -> list[dict]:
    """Wellness tools, entity memory (libsql), and sandbox filesystem."""
    uid = user_id.strip().lower()
    return [
        {
            "command": "uv",
            "args": ["run", "wellness_server.py"],
            "cwd": str(BASE_DIR),
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{uid}.db"},
            "cwd": str(BASE_DIR),
        },
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str(BASE_DIR / "sandbox")],
            "cwd": str(BASE_DIR),
        },
    ]


def librarian_mcp_server_params() -> list[dict]:
    """Fetch-based reading of public pages; combined with strict prompts + allowlisted fetch tool on coach."""
    return [
        {
            "command": "uvx",
            "args": ["mcp-server-fetch"],
            "cwd": str(BASE_DIR),
        },
    ]
