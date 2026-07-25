"""Filesystem tools scoped to a single repository root (no shell, no path escape)."""

from __future__ import annotations

import glob
from pathlib import Path


def make_repo_tools(root: Path):
    root = root.resolve()
    max_read_bytes = 256_000

    def _under_root(rel: str) -> Path:
        if not rel or rel.startswith(("/", "\\")):
            raise ValueError("relative path only; no absolute paths")
        candidate = (root / rel).resolve()
        candidate.relative_to(root)
        return candidate

    async def list_directory(relative_path: str = ".") -> str:
        """List file and directory names directly inside relative_path (default: project root)."""
        try:
            d = _under_root(relative_path)
            if not d.is_dir():
                return f"Not a directory: {relative_path}"
            names = sorted(p.name for p in d.iterdir())
            return "\n".join(names) if names else "(empty)"
        except Exception as e:
            return f"Error: {e}"

    async def read_text_file(relative_path: str) -> str:
        """Read a UTF-8 text file under the project root (size-capped)."""
        try:
            p = _under_root(relative_path)
            if not p.is_file():
                return f"Not a file: {relative_path}"
            data = p.read_bytes()
            if len(data) > max_read_bytes:
                return f"File too large ({len(data)} bytes); cap is {max_read_bytes}"
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error: {e}"

    async def path_exists(relative_path: str) -> str:
        """Return whether a path exists under the project root (file or directory)."""
        try:
            p = _under_root(relative_path)
            if p.exists():
                kind = "dir" if p.is_dir() else "file"
                return f"yes ({kind})"
            return "no"
        except Exception as e:
            return f"Error: {e}"

    async def glob_relative(pattern: str) -> str:
        """Glob for paths under the root. Pattern is relative, e.g. '*.py' or 'src/**/*.md'."""
        try:
            if pattern.startswith(("/", "\\")) or pattern.startswith(".."):
                return "Invalid pattern: use a relative glob under the project root."
            matches = sorted({Path(p).resolve() for p in glob.glob(str(root / pattern), recursive=True)})
            rels: list[str] = []
            for m in matches:
                try:
                    rels.append(str(m.relative_to(root)))
                except ValueError:
                    continue
            return "\n".join(rels) if rels else "(no matches)"
        except Exception as e:
            return f"Error: {e}"

    return [list_directory, read_text_file, path_exists, glob_relative]
