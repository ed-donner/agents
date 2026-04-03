from __future__ import annotations

import logging
from pathlib import Path

from asket_mcp.config import get_settings

logger = logging.getLogger(__name__)


def brain_root() -> Path:
    r = get_settings().brain_root
    if not r.is_absolute():
        r = Path.cwd() / r
    root = r.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_resolve(relative_path: str) -> Path:
    rel = (relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel or rel == ".":
        return brain_root()
    root = brain_root()
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Path escapes the Brain folder (not allowed).")
    return candidate


def brain_read_text(relative_path: str) -> str:
    path = safe_resolve(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"Not a file: {relative_path!r}")
    return path.read_text(encoding="utf-8", errors="replace")


def brain_write_markdown(relative_path: str, content: str, overwrite: bool = False) -> str:
    path = safe_resolve(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_file() and not overwrite:
        raise FileExistsError(
            "File already exists. Set overwrite=true only after the human explicitly approves replacing it."
        )
    path.write_text(content, encoding="utf-8")
    logger.info("brain write: %s", path)
    return str(path.relative_to(brain_root()))


def brain_list_directory(relative_path: str = ".", max_entries: int = 200) -> str:
    d = safe_resolve(relative_path)
    if not d.is_dir():
        raise NotADirectoryError(f"Not a directory: {relative_path!r}")
    lines: list[str] = []
    n = 0
    for child in sorted(d.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if n >= max_entries:
            lines.append(f"... ({max_entries} entries shown, directory truncated)")
            break
        kind = "dir" if child.is_dir() else "file"
        rel = child.relative_to(brain_root())
        lines.append(f"{kind}\t{rel}")
        n += 1
    return "\n".join(lines) if lines else "(empty directory)"


def brain_delete_file(relative_path: str, user_confirmed_deletion: bool = False) -> str:
    if not user_confirmed_deletion:
        raise PermissionError(
            "Deletion blocked: set user_confirmed_deletion=true only after the user explicitly approves."
        )
    path = safe_resolve(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"Not a file: {relative_path!r}")
    path.unlink()
    logger.info("brain delete: %s", path)
    return f"Deleted {path.relative_to(brain_root())}"


def brain_search_markdown(query: str, under_subpath: str = ".", max_file_hits: int = 40) -> str:
    q = (query or "").strip().lower()
    if not q:
        return "No matches in .md files under that path."
    base = safe_resolve(under_subpath)
    if not base.is_dir():
        raise NotADirectoryError(f"Not a directory: {under_subpath!r}")
    root = brain_root()
    results: list[str] = []
    scan_limit = 500
    n_scanned = 0
    for path in sorted(base.rglob("*.md")):
        if not path.is_file():
            continue
        n_scanned += 1
        if n_scanned > scan_limit:
            results.append("... (scan limit reached)")
            break
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        i = lower.find(q)
        if i < 0:
            continue
        if len(results) >= max_file_hits:
            results.append(f"... ({max_file_hits} matches max)")
            break
        rel = path.relative_to(root)
        snippet = text[max(0, i - 80) : min(len(text), i + len(q) + 120)].replace("\n", " ")
        results.append(f"{rel}\n  … {snippet} …")
    return "\n\n".join(results) if results else "No matches in .md files under that path."


def brain_find_files(under_subpath: str = ".", file_glob: str = "*.md", max_files: int = 200) -> str:
    base = safe_resolve(under_subpath)
    if not base.is_dir():
        raise NotADirectoryError(f"Not a directory: {under_subpath!r}")
    names: list[str] = []
    for path in base.rglob(file_glob):
        if not path.is_file():
            continue
        rel = path.relative_to(brain_root())
        names.append(str(rel))
        if len(names) >= max_files:
            names.append(f"... ({max_files} paths shown)")
            break
    return "\n".join(names) if names else "No files matched."
