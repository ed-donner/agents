"""Stdio MCP server launch params: uv run with cwd at this project root."""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent


def mcp_stdio_params(script_name: str) -> dict:
    script = _PROJECT_ROOT / script_name
    return {
        "command": "uv",
        "args": ["run", str(script)],
        "cwd": str(_PROJECT_ROOT),
    }
