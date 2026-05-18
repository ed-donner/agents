"""Read-only repository exploration helpers (used by the MCP server)."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path


def repo_root_from_env() -> Path | None:
    raw = (os.environ.get("REPO_ONBOARDING_ROOT") or "").strip()
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        return None
    return root


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


def list_directory(root: Path, relative_path: str = ".") -> str:
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


def read_file_text(root: Path, relative_path: str, max_chars: int = 80000) -> str:
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


def search_text(
    root: Path,
    query: str,
    file_glob: str = "*",
    max_matches: int = 40,
) -> str:
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
        if path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc", ".so", ".dylib", ".exe"
        }:
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


def repo_summary(root: Path) -> str:
    top = sorted(root.iterdir())[:50]
    names = [p.name + ("/" if p.is_dir() else "") for p in top]
    hints: list[str] = []
    for p in (
        root / "README.md",
        root / "README.rst",
        root / "README",
        root / "pyproject.toml",
        root / "package.json",
        root / "requirements.txt",
        root / "Makefile",
    ):
        if p.is_file():
            hints.append(str(p.relative_to(root)))
    return (
        f"Root: {root}\n\nTop-level:\n"
        + "\n".join(names)
        + "\n\nNotable files: "
        + (", ".join(hints) or "(none detected)")
    )
