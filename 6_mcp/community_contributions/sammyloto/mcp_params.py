"""
Stdio MCP server params for wiring `agronomy_advisor` into an OpenAI Agents `MCPServerStdio`.

Example:
    from mcp_params import agronomy_mcp_server_params
    MCPServerStdio(params=agronomy_mcp_server_params(), ...)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def agronomy_mcp_server_params() -> dict:
    """Launch the local agronomy MCP server (stdio)."""
    py = shutil.which("python3") or shutil.which("python") or "python3"
    # Prefer explicit PYTHON if set (e.g. venv)
    cmd = os.environ.get("PYTHON", py)
    return {
        "command": cmd,
        "args": [str(_ROOT / "mcp_server.py")],
        "cwd": str(_ROOT),
    }
