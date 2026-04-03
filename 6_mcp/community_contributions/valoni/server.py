from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mini-dev-assistant")
ROOT = Path.cwd().resolve()


def safe_path(rel_path: str) -> Path:
    path = (ROOT / rel_path).resolve()
    if not str(path).startswith(str(ROOT)):
        raise ValueError("Path outside project root")
    return path


@mcp.tool()
def list_files(path: str = ".") -> str:
    target = safe_path(path)

    if not target.exists():
        return f"Path does not exist: {path}"

    if target.is_file():
        return str(target.relative_to(ROOT))

    items = []
    for item in sorted(target.iterdir()):
        name = item.relative_to(ROOT)
        if item.name in {".git", ".venv", "__pycache__", "node_modules"}:
            continue
        suffix = "/" if item.is_dir() else ""
        items.append(f"{name}{suffix}")

    return "\n".join(items) if items else "(empty)"


@mcp.tool()
def read_file(path: str) -> str:
    target = safe_path(path)

    if not target.exists() or not target.is_file():
        return f"File not found: {path}"

    return target.read_text(encoding="utf-8", errors="replace")[:20000]


@mcp.tool()
def search_in_files(query: str, path: str = ".") -> str:
    target = safe_path(path)

    if not target.exists():
        return f"Path does not exist: {path}"

    matches = []

    for file in target.rglob("*"):
        if not file.is_file():
            continue
        if any(part in {".git", ".venv", "__pycache__", "node_modules"} for part in file.parts):
            continue

        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for i, line in enumerate(text.splitlines(), start=1):
            if query.lower() in line.lower():
                matches.append(f"{file.relative_to(ROOT)}:{i}: {line.strip()}")
                if len(matches) >= 50:
                    return "\n".join(matches)

    return "\n".join(matches) if matches else "No matches found."


if __name__ == "__main__":
    mcp.run(transport="stdio")