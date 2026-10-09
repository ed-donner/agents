"""MCP server: list and read *.md study notes in this folder (Week 6 exercise)."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

_ROOT = Path(__file__).resolve().parent


def _safe_note_path(filename: str) -> Path:
    """Only allow basenames under _ROOT (same directory as this file)."""
    name = Path(filename).name
    path = (_ROOT / name).resolve()
    root = _ROOT.resolve()
    try:
        path.relative_to(root)
    except ValueError as e:
        raise ValueError("Path must stay in the exercise folder") from e
    if path.suffix.lower() != ".md":
        raise ValueError("Only .md files are allowed")
    return path


mcp = FastMCP("study_server")


@mcp.tool()
async def list_study_notes() -> list[str]:
    """List markdown filenames in the exercise folder.

    Returns:
        Filenames ending in .md for read_study_note.
    """
    return sorted(p.name for p in _ROOT.glob("*.md"))


@mcp.tool()
async def read_study_note(filename: str) -> str:
    """Read one markdown note from the exercise folder.

    Args:
        filename: e.g. mcp_basics.md (from list_study_notes).
    """
    path = _safe_note_path(filename)
    if not path.is_file():
        return f"Note not found: {filename}"
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
