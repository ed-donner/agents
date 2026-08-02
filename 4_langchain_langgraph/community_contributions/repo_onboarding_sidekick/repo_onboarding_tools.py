import fnmatch
from pathlib import Path

from langchain_core.tools import tool


def _resolve_under_root(root: Path, relative: str) -> Path:
    rel = (relative or ".").strip() or "."
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError("Path must be relative to the repository root.")
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as e:
        raise ValueError("Path escapes repository root.") from e
    return candidate


def make_repo_tools(repo_root: str):
    root = Path(repo_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    @tool
    def list_repo_directory(relative_path: str = ".") -> str:
        """List files and immediate subdirectories under relative_path within the repo. Use '.' for the repository root."""
        try:
            target = _resolve_under_root(root, relative_path)
        except ValueError as e:
            return f"Error: {e}"
        if not target.exists():
            return f"Path does not exist: {relative_path}"
        if target.is_file():
            return f"Not a directory: {relative_path}"
        lines: list[str] = []
        try:
            for p in sorted(target.iterdir())[:200]:
                name = p.name + ("/" if p.is_dir() else "")
                lines.append(name)
        except PermissionError as e:
            return f"Permission denied: {e}"
        if not lines:
            return "(empty)"
        return "\n".join(lines)

    @tool
    def read_repo_file(relative_path: str, max_chars: int = 80000) -> str:
        """Read a text file from the repo (relative path). Truncates very large files. Skips obvious binary files."""
        try:
            target = _resolve_under_root(root, relative_path)
        except ValueError as e:
            return f"Error: {e}"
        if not target.is_file():
            return f"Not a file (or missing): {relative_path}"
        max_bytes = min(max_chars * 4, 500_000)
        try:
            with open(target, "rb") as f:
                raw = f.read(max_bytes)
        except OSError as e:
            return f"Error reading file: {e}"
        if b"\x00" in raw[:8192]:
            return "(binary file — skipped)"
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        if len(text) > max_chars:
            return text[:max_chars] + f"\n\n... [truncated {len(text) - max_chars} chars]"
        return text

    @tool
    def search_repo_text(
        query: str,
        file_glob: str = "*",
        max_matches: int = 40,
    ) -> str:
        """Search for a substring in text files under the repo (case-insensitive). file_glob defaults to '*' (e.g. '*.py', '*.md')."""
        if not query or len(query) > 200:
            return "Query must be 1–200 characters."
        q = query.lower()
        matches: list[str] = []
        count = 0
        skip_parts = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        for path in root.rglob("*"):
            if count >= max_matches:
                break
            if any(part in skip_parts for part in path.parts):
                continue
            if not path.is_file():
                continue
            if not fnmatch.fnmatch(path.name, file_glob) and file_glob != "*":
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc", ".so", ".dylib", ".exe"}:
                continue
            try:
                with open(path, "rb") as f:
                    data = f.read(64_000)
            except OSError:
                continue
            if b"\x00" in data[:512]:
                continue
            try:
                text = data.decode("utf-8", errors="ignore")
            except Exception:
                continue
            lower = text.lower()
            idx = lower.find(q)
            if idx == -1:
                continue
            rel = path.relative_to(root)
            line = text[: idx + 1].count("\n") + 1
            snippet = text[max(0, idx - 60) : idx + len(query) + 60].replace("\n", " ")
            matches.append(f"{rel}:{line}: {snippet}")
            count += 1
        if not matches:
            return "No matches."
        return "\n".join(matches)

    @tool
    def repo_summary() -> str:
        """Return repository root path, top-level directory names, and presence of common files (README, pyproject, package.json)."""
        top = sorted(root.iterdir())[:50]
        names = [p.name + ("/" if p.is_dir() else "") for p in top]
        hints = []
        for p in (root / "README.md", root / "README.rst", root / "README", root / "pyproject.toml", root / "package.json", root / "requirements.txt", root / "Makefile"):
            if p.is_file():
                hints.append(str(p.relative_to(root)))
        return f"Root: {root}\n\nTop-level:\n" + "\n".join(names) + "\n\nNotable files: " + (", ".join(hints) or "(none detected)")

    return [list_repo_directory, read_repo_file, search_repo_text, repo_summary]
