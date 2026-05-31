"""
MCP server: read-only exploration of a local repository.

Set REPO_ONBOARDING_ROOT to an absolute path before starting (the agent demo passes this via subprocess env).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from repo_logic import (
    list_directory,
    read_file_text,
    repo_root_from_env,
    repo_summary,
    search_text,
)

mcp = FastMCP("repo_onboarding")


def _require_root():
    root = repo_root_from_env()
    if root is None:
        raise ValueError(
            "REPO_ONBOARDING_ROOT is not set or is not a directory. "
            "Set it to the repository root (absolute path) before starting this server."
        )
    return root


@mcp.tool()
async def list_repo_directory(relative_path: str = ".") -> str:
    """List files and immediate subdirectories under relative_path within the repo. Use '.' for the repository root."""
    try:
        root = _require_root()
    except ValueError as e:
        return str(e)
    return list_directory(root, relative_path)


@mcp.tool()
async def read_repo_file(relative_path: str, max_chars: int = 80000) -> str:
    """Read a text file from the repo (relative path). Large files are truncated; binary files are skipped."""
    try:
        root = _require_root()
    except ValueError as e:
        return str(e)
    return read_file_text(root, relative_path, max_chars=max_chars)


@mcp.tool()
async def search_repo_text(
    query: str,
    file_glob: str = "*",
    max_matches: int = 40,
) -> str:
    """Search for a substring in text files (case-insensitive). Optional file_glob e.g. '*.py' or '*.md'."""
    try:
        root = _require_root()
    except ValueError as e:
        return str(e)
    return search_text(root, query, file_glob=file_glob, max_matches=max_matches)


@mcp.tool()
async def summarize_repo() -> str:
    """Summarize repo root: path, top-level entries, and common manifest files if present."""
    try:
        root = _require_root()
    except ValueError as e:
        return str(e)
    return repo_summary(root)


@mcp.resource("repo-onboarding://root")
def resource_repo_root() -> str:
    """Resolved repository root path from REPO_ONBOARDING_ROOT."""
    root = repo_root_from_env()
    if root is None:
        return "REPO_ONBOARDING_ROOT is not set or invalid."
    return str(root)


if __name__ == "__main__":
    mcp.run(transport="stdio")
