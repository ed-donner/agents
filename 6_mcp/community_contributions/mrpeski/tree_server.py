from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tree_server")


def _build_tree(root: Path, max_depth: int, prefix: str = "", depth: int = 0) -> str:
    if depth > max_depth:
        return ""

    lines = []

    if depth == 0:
        lines.append(str(root.resolve()))

    try:
        entries = sorted(root.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except PermissionError:
        lines.append(prefix + "└── [permission denied]")
        return "\n".join(lines)

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir() and not entry.is_symlink():
            extension = "    " if is_last else "│   "
            subtree = _build_tree(entry, max_depth, prefix + extension, depth + 1)
            if subtree:
                lines.append(subtree)

    return "\n".join(lines)


@mcp.tool()
def tree(path: str = ".", max_depth: int = 5) -> str:
    """
    Return a tree view of a directory.

    Args:
        path: Directory to inspect. Defaults to '.' (current working directory).
        max_depth: How deep to recurse. Defaults to 5.
    """
    root = Path(path).expanduser().resolve()

    if not root.exists():
        return f"Error: path '{path}' does not exist."
    if not root.is_dir():
        return f"Error: '{path}' is not a directory."

    return _build_tree(root, max_depth)


if __name__ == "__main__":
    mcp.run(transport='stdio')