"""Path-jailed filesystem helpers for the Kirundi Markdown corpus."""

from __future__ import annotations

from pathlib import Path


def resolve_under_root(root: Path, relative: str) -> Path:
    """Resolve a relative path; raise ValueError if it escapes root."""
    rel = (relative or ".").strip() or "."
    parts = Path(rel).parts
    if rel.startswith("/") or ".." in parts:
        raise ValueError("Path must be relative to the Brain root (no '..').")
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Path escapes Brain root.") from exc
    return candidate


def list_directory(root: Path, relative_path: str = ".", max_entries: int = 200) -> str:
    """List entries under a Brain-relative path."""
    try:
        target = resolve_under_root(root, relative_path)
    except ValueError as exc:
        return f"Error: {exc}"
    if not target.exists():
        return f"Path does not exist: {relative_path}"
    if target.is_file():
        return f"Not a directory: {relative_path}"
    names: list[str] = []
    try:
        for path in sorted(target.iterdir())[:max_entries]:
            names.append(path.name + ("/" if path.is_dir() else ""))
    except OSError as exc:
        return f"Error listing directory: {exc}"
    return "\n".join(names) if names else "(empty)"


def read_text(root: Path, relative_path: str, max_chars: int = 40_000) -> str:
    """Read a UTF-8 text file from the Brain."""
    try:
        target = resolve_under_root(root, relative_path)
    except ValueError as exc:
        return f"Error: {exc}"
    if not target.is_file():
        return f"Not a file (or missing): {relative_path}"
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error reading file: {exc}"
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n... [truncated {len(text) - max_chars} chars]"
    return text


def write_markdown(
    root: Path,
    relative_path: str,
    content: str,
    *,
    overwrite: bool = False,
) -> str:
    """Write Markdown into the Brain; require overwrite=True to replace."""
    try:
        target = resolve_under_root(root, relative_path)
    except ValueError as exc:
        return f"Error: {exc}"
    if target.exists() and not overwrite:
        return (
            f"File exists: {relative_path}. "
            "Set overwrite=true only after the learner confirms replacement."
        )
    if target.exists() and target.is_dir():
        return f"Error: path is a directory: {relative_path}"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"Error writing file: {exc}"
    return f"Wrote Brain file: {relative_path}"


def delete_file(root: Path, relative_path: str, *, confirmed: bool = False) -> str:
    """Delete a Brain file; require confirmed=True after explicit approval."""
    if not confirmed:
        return (
            "Deletion blocked. Set user_confirmed_deletion=true "
            "only after the learner explicitly approves."
        )
    try:
        target = resolve_under_root(root, relative_path)
    except ValueError as exc:
        return f"Error: {exc}"
    if not target.is_file():
        return f"Not a file (or missing): {relative_path}"
    try:
        target.unlink()
    except OSError as exc:
        return f"Error deleting file: {exc}"
    return f"Deleted Brain file: {relative_path}"


def search_markdown(
    root: Path,
    query: str,
    under_subpath: str = ".",
    max_file_hits: int = 20,
) -> str:
    """Case-insensitive keyword search across .md files under the Brain."""
    needle = (query or "").strip()
    if not needle:
        return "Error: query is empty."
    try:
        base = resolve_under_root(root, under_subpath)
    except ValueError as exc:
        return f"Error: {exc}"
    if not base.exists():
        return f"Path does not exist: {under_subpath}"

    hits: list[str] = []
    files = sorted(base.rglob("*.md")) if base.is_dir() else []
    if base.is_file() and base.suffix == ".md":
        files = [base]

    for path in files:
        if len(hits) >= max_file_hits:
            break
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lower = text.lower()
        q = needle.lower()
        if q not in lower:
            continue
        idx = lower.find(q)
        start = max(0, idx - 60)
        end = min(len(text), idx + len(needle) + 60)
        snippet = text[start:end].replace("\n", " ")
        rel = path.relative_to(root.resolve()).as_posix()
        hits.append(f"- {rel}: ...{snippet}...")

    if not hits:
        return f"No matches for {needle!r}."
    return f"Found {len(hits)} file(s):\n" + "\n".join(hits)


def collect_context(root: Path, query: str, max_chars: int = 6_000) -> str:
    """Gather Markdown snippets for RAG-style tutoring."""
    search_result = search_markdown(root, query, max_file_hits=8)
    if search_result.startswith("No matches") or search_result.startswith("Error"):
        # Fall back to concatenating short lesson intros.
        parts: list[str] = []
        for path in sorted(root.rglob("*.md"))[:6]:
            try:
                body = path.read_text(encoding="utf-8")[:800]
            except OSError:
                continue
            rel = path.relative_to(root.resolve()).as_posix()
            parts.append(f"### {rel}\n{body}")
        blob = "\n\n".join(parts)
        return blob[:max_chars] if blob else "Corpus is empty."
    return search_result[:max_chars]
